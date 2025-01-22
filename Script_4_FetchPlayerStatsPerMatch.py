from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
matches_collection = db['matches']
players_collection = db['players']

# Setup Selenium WebDriver with Service
driver_path = '/Users/petercorcoran/final_year_project/chromedriver'
service = Service(driver_path)  # Use the Service class
driver = webdriver.Chrome(service=service)  # Initialize Chrome WebDriver

# Function to fetch player statistics using Selenium


def get_player_statistics(match_id, player_id):
    """Fetch player statistics using Selenium."""
    url = f"https://www.sofascore.com/api/v1/event/{
        match_id}/player/{player_id}/statistics"
    driver.get(url)

    # Wait for the data to load (if necessary)
    try:
        # Adjust the wait time and conditions based on the page's behavior
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Extract the page source and parse it as JSON
        page_source = driver.find_element(By.TAG_NAME, "body").text
        return json.loads(page_source)
    except Exception as e:
        print(f"Error fetching statistics for player {
              player_id} in match {match_id}: {e}")
        return None

# Function to store player stats in MongoDB


def store_player_stats_in_round_collection(round_number, player_id, player_stats, match_id):
    collection_name = f"round_{round_number}"
    round_collection = db[collection_name]

    player_stats_document = {
        '_id': player_id,
        'match_id': match_id,
        **player_stats.get('statistics', {})
    }

    round_collection.update_one(
        {'_id': player_id, 'match_id': match_id},
        {'$set': player_stats_document},
        upsert=True
    )
    print(f"Stored stats for player {player_id} in match {
          match_id}, round {round_number}.")

# Function to process each match


def process_match(match):
    match_id = match['_id']
    home_team_id = match['homeTeam']['id']
    away_team_id = match['awayTeam']['id']
    round_number = match['roundInfo']['round']

    for team_id in [home_team_id, away_team_id]:
        players = players_collection.find(
            {'team.id': team_id}, {'_id': 1, 'name': 1})
        for player in players:
            player_id = player.get('id', player['_id'])
            player_stats = get_player_statistics(match_id, player_id)
            if player_stats:
                store_player_stats_in_round_collection(
                    round_number, player_id, player_stats, match_id)

# Fetch and process matches for specific rounds


def fetch_and_store_player_stats_for_specific_rounds(rounds):
    matches = matches_collection.find({"roundInfo.round": {"$in": rounds}})
    for match in matches:
        process_match(match)


# Run the process for rounds 21 and 22
fetch_and_store_player_stats_for_specific_rounds([21, 22])

# Close the browser
driver.quit()
