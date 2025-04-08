import time
import json
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
matches_collection = db['matches']

# Selenium setup
driver_path = '/Users/petercorcoran/final_year_project/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

INCIDENTS_URL_TEMPLATE = "https://www.sofascore.com/api/v1/event/{match_id}/incidents"


def get_match_incidents(match_id):
    url = INCIDENTS_URL_TEMPLATE.format(match_id=match_id)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.find_element(By.TAG_NAME, "body").text
        data = json.loads(page_source)
        return data.get('incidents', [])
    except Exception as e:
        print(f"Error fetching incidents for match {match_id}: {e}")
        return []


def store_card_incidents(round_number, match_id, player_id, card_data):
    collection_name = f"round_{round_number}"
    round_collection = db[collection_name]

    # Update the player's document and push card incidents to the array
    round_collection.update_one(
        {'_id': player_id, 'match_id': match_id},
        {
            '$set': {'match_id': match_id},
            '$push': {'cards': card_data}
        },
        upsert=True
    )
    print(f"Stored card for player {player_id} in match {
          match_id}, round {round_number}.")


def fetch_and_store_cards_for_matches(min_round=22, max_round=29):
    query = {"roundInfo.round": {"$gte": min_round, "$lte": max_round}}
    matches = matches_collection.find(query)

    for match in matches:
        match_id = match["_id"]
        round_number = match["roundInfo"]["round"]
        incidents = get_match_incidents(match_id)

        card_incidents = [
            inc for inc in incidents
            if inc.get("incidentType") == "card" and inc.get("incidentClass") in ("yellow", "red")
        ]

        for card in card_incidents:
            player = card.get("player", {})
            player_id = player.get("id")
            if player_id:
                card_data = {
                    "time": card.get("time"),
                    "reason": card.get("reason"),
                    "incidentClass": card.get("incidentClass"),
                    "incidentType": card.get("incidentType")
                }
                store_card_incidents(
                    round_number, match_id, player_id, card_data)

        time.sleep(1)


try:
    fetch_and_store_cards_for_matches(23, 29)
finally:
    driver.quit()
