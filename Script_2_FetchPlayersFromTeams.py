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
players_collection = db['players']  # Collection storing player information

# Base URL for player API
BASE_PLAYER_URL = "https://api.sofascore.com/api/v1/player"

# ---------------------------------------------------------------------
# 1) Setup Selenium WebDriver
# ---------------------------------------------------------------------
# Adjust the path to your local ChromeDriver
driver_path = '/Users/petercorcoran/python/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 2) Function to fetch player information using Selenium
# ---------------------------------------------------------------------


def fetch_player_info(player_id):
    """
    Navigates to the Sofascore player API endpoint in Chrome
    and returns the player's data as JSON.
    """
    url = f"{BASE_PLAYER_URL}/{player_id}/"
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

        # Ensure we return the 'player' data
        return response_data.get('player', {})
    except Exception as e:
        print(f"Error fetching data for player {player_id}: {e}")
        return {}

# ---------------------------------------------------------------------
# 3) Function to update player information in MongoDB
# ---------------------------------------------------------------------


def update_player_info():
    """
    Updates player information in MongoDB by fetching data
    using Selenium for all distinct player IDs in the collection.
    """
    player_ids = players_collection.distinct('_id')  # Get all player IDs

    for player_id in player_ids:
        print(f"Fetching data for player ID: {player_id}")

        # Fetch player data
        player_data = fetch_player_info(player_id)

        if player_data:
            # Prepare player document for MongoDB
            player_data['_id'] = player_data.pop('id')  # Ensure '_id' is set
            try:
                # Update or insert player data in MongoDB
                players_collection.replace_one(
                    {'_id': player_data['_id']}, player_data, upsert=True
                )
                print(f"Updated player data for ID {player_data['_id']}")
            except Exception as e:
                print(f"Error updating data for player ID {
                      player_data['_id']}: {e}")
        else:
            print(f"No valid data found for player ID: {player_id}")

        # Implement a delay to avoid rate-limiting
        time.sleep(2)


# ---------------------------------------------------------------------
# 4) Main Execution
# ---------------------------------------------------------------------
try:
    update_player_info()
finally:
    # Make sure to close the browser at the end
    driver.quit()
