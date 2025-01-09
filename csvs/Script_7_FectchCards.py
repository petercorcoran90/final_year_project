import time
import json
from pymongo import MongoClient

# ----- [ Selenium Imports ] -----
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------------------------------------
# 1) MongoDB Setup
# ---------------------------------------------------------------------
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']

matches_collection = db['matches']  # Where all matches are stored

# Base URL for incidents endpoint
INCIDENTS_URL_TEMPLATE = "https://www.sofascore.com/api/v1/event/{match_id}/incidents"

# ---------------------------------------------------------------------
# 2) Setup Selenium WebDriver
# ---------------------------------------------------------------------
driver_path = '/Users/petercorcoran/python/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 3) Function to fetch incidents for a given match
# ---------------------------------------------------------------------


def get_match_incidents(match_id):
    """
    Fetch all incidents for a specific match using Selenium,
    and return them as a list of incident objects.
    """
    url = INCIDENTS_URL_TEMPLATE.format(match_id=match_id)
    try:
        driver.get(url)

        # Wait for the <body> to load (adjust timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_source = driver.find_element(By.TAG_NAME, "body").text
        data = json.loads(page_source)

        # 'incidents' array in the JSON
        incidents = data.get('incidents', [])
        return incidents

    except Exception as e:
        print(f"Error fetching incidents for match {match_id}: {e}")
        return []

# ---------------------------------------------------------------------
# 4) Function to store a single card incident in the round_X collection
# ---------------------------------------------------------------------


def store_player_card_in_round_collection(round_number, match_id, player_id, card_data):
    collection_name = f"round_{round_number}"
    round_collection = db[collection_name]

    # Build a unique doc ID based on player_id and match_id
    doc_id = f"{player_id}_{match_id}"

    update_query = {"_id": doc_id}
    update_operation = {
        # Make sure we store reference fields in the doc
        "$set": {
            "player_id": player_id,
            "match_id": match_id
        },
        # Push the new card data into the 'cards' array
        "$push": {"cards": card_data}
    }

    round_collection.update_one(update_query, update_operation, upsert=True)
    print(
        f"Stored {card_data['incidentClass']} card for player {player_id} "
        f"in match {match_id}, round {
            round_number} in collection {collection_name}."
    )


# ---------------------------------------------------------------------
# 5) Main function: fetch & store card incidents for all matches
# ---------------------------------------------------------------------


def fetch_and_store_cards_for_all_matches(min_round=1, max_round=20):
    """
    Loops through all matches in 'matches_collection' with round in [min_round, max_round],
    fetches incidents, filters out 'incidentType': 'card' with 'incidentClass' in ['yellow','red'],
    and stores them in the appropriate 'round_X' collection under each player's doc.
    """
    # Only get matches whose round is between min_round and max_round (inclusive)
    filter_query = {
        "roundInfo.round": {
            "$gte": min_round,
            "$lte": max_round
        }
    }
    all_matches = matches_collection.find(filter_query)

    for match in all_matches:
        match_id = match["_id"]
        round_number = match.get("roundInfo", {}).get("round", 0)

        # 1) Get all incidents for this match
        incidents = get_match_incidents(match_id)

        # 2) Filter out only card incidents
        #    (incidentType: "card", incidentClass in ["yellow", "red"])
        card_incidents = [
            inc for inc in incidents
            if inc.get("incidentType") == "card"
            and inc.get("incidentClass") in ("yellow", "red")
        ]

        if not card_incidents:
            print(
                f"No yellow/red cards found for match {match_id} (round {round_number}).")
            continue

        print(
            f"Found {len(card_incidents)} card(s) in match {
                match_id} (round {round_number})."
        )

        # 3) For each card, identify the player and store the card
        for card_incident in card_incidents:
            player_data = card_incident.get("player")
            if not player_data:
                print(f"No 'player' field in card incident: {card_incident}")
                continue

            player_id = player_data.get("id")
            if not player_id:
                print(f"No 'id' field in player object: {player_data}")
                continue

            # We'll store any relevant info about the card
            card_data = {
                "time": card_incident.get("time"),
                "reason": card_incident.get("reason"),
                # "yellow" or "red"
                "incidentClass": card_incident.get("incidentClass"),
                "incidentType": card_incident.get("incidentType"),    # "card"
            }

            store_player_card_in_round_collection(
                round_number,
                match_id,
                player_id,
                card_data
            )

        # Optional: add a small delay to avoid rate-limiting
        time.sleep(1)


# ---------------------------------------------------------------------
# 6) Run the script and close the browser
# ---------------------------------------------------------------------
try:
    fetch_and_store_cards_for_all_matches()
finally:
    driver.quit()
