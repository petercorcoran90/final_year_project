import time
import json
from pymongo import MongoClient

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']  # Use your database name
# Assuming your collection is called 'players'
players_collection = db['players']

# Sofascore API URL template
SOFASCORE_API_URL = "https://www.sofascore.com/api/v1/player/{player_id}/characteristics"

# Setup Selenium WebDriver
driver_path = '/Users/petercorcoran/python/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)


def fetch_player_position_from_api(player_id):
    """
    Fetch player's positions from the Sofascore API
    by navigating to the endpoint in Chrome.
    """
    url = SOFASCORE_API_URL.format(player_id=player_id)
    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_source = driver.find_element(By.TAG_NAME, "body").text
        data = json.loads(page_source)

        # Now positions can be something like ["AM","RW"]
        positions = data.get('positions', [])
        if positions:
            return positions
    except Exception as e:
        print(f"Error fetching data for player {player_id}: {e}")

    return []


def update_player_positions(player_id, new_positions):
    """
    Update the player's positions in MongoDB as a list (e.g. ["AM","RW"]).
    """
    result = players_collection.update_one(
        {'_id': player_id},
        {'$set': {'positions': new_positions}}
    )
    if result.modified_count > 0:
        print(f"Updated positions for player {player_id} to {new_positions}")
    else:
        print(f"No update made for player {
              player_id}. Positions already up-to-date.")


def update_all_players_positions():
    players = players_collection.find({}, {"_id": 1, "name": 1})

    for player in players:
        player_id = player['_id']
        player_name = player.get('name', 'Unknown')

        new_positions = fetch_player_position_from_api(player_id)
        if new_positions:
            print(f"Player: {player_name}, New Positions: {new_positions}")
            update_player_positions(player_id, new_positions)
        else:
            print(f"Could not fetch positions for player {
                  player_name} (ID: {player_id})")

        # Optional delay
        time.sleep(1)


if __name__ == "__main__":
    try:
        update_all_players_positions()
    finally:
        driver.quit()
