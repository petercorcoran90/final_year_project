import time
import json
from pymongo import MongoClient

# ----- [ Selenium Imports ] -----
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
teams_collection = db['teams']
players_collection = db['players']

# Base URL for team players API
BASE_TEAM_URL = "https://api.sofascore.com/api/v1/team"

# ---------------------------------------------------------------------
# 1) Setup Selenium WebDriver
# ---------------------------------------------------------------------
# Adjust the path to your local ChromeDriver
driver_path = '/Users/petercorcoran/python/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 2) Function to get players for a team using Selenium
# ---------------------------------------------------------------------


def get_team_players(team_id):
    """
    Navigates to the Sofascore team players API endpoint in Chrome
    and returns the list of players as JSON data.
    """
    url = f"{BASE_TEAM_URL}/{team_id}/players"
    try:
        # Go to the URL with Selenium
        driver.get(url)

        # Wait until the body is present (you can adjust conditions/time as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract the raw text from the page body
        page_source = driver.find_element(By.TAG_NAME, "body").text

        # Parse the text as JSON
        response_data = json.loads(page_source)

        # Extract 'players' array and within it, each 'player'
        players_data = response_data.get('players', [])
        return [p['player'] for p in players_data]
    except Exception as e:
        print(f"Error fetching players for team {team_id}: {e}")
        return []

# ---------------------------------------------------------------------
# 3) Function to store team players in MongoDB
# ---------------------------------------------------------------------


def store_team_players_in_mongodb():
    teams = teams_collection.find({})  # Get all teams from MongoDB

    for team in teams:
        team_id = team['_id']  # Team ID (also MongoDB _id)
        team_name = team['name']
        print(f"Fetching players for team: {team_name} (ID: {team_id})")

        # Get players for the current team using Selenium
        players = get_team_players(team_id)

        if players:
            for player in players:
                # Use 'id' as the MongoDB '_id'
                player['_id'] = player.pop('id')
                player['team_id'] = team_id

                # Check if the player already exists in the MongoDB collection
                if not players_collection.find_one({'_id': player['_id']}):
                    # Insert the player into MongoDB if it doesn't exist
                    players_collection.insert_one(player)
                    print(f"Stored player: {
                          player['name']} (ID: {player['_id']})")
                else:
                    print(f"Player {player['name']
                                    } already exists in the database.")
        else:
            print(f"No players found for team {team_name}")

        # Implement a delay to avoid any potential rate-limiting or page load issues
        time.sleep(2)


# ---------------------------------------------------------------------
# 4) Main Execution
# ---------------------------------------------------------------------
try:
    store_team_players_in_mongodb()
finally:
    # Make sure to close the browser at the end
    driver.quit()
