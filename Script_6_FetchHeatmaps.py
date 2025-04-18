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

# If you store match stats in "round_1", "round_2", etc.
# those collections are created dynamically below.
matches_collection = db['matches']  # Contains match docs

# Endpoint for heatmap:
# https://www.sofascore.com/api/v1/event/{match_id}/player/{player_id}/heatmap
HEATMAP_URL_TEMPLATE = (
    "https://www.sofascore.com/api/v1/event/{match_id}/player/{player_id}/heatmap"
)

# ---------------------------------------------------------------------
# 2) Setup Selenium WebDriver
# ---------------------------------------------------------------------
driver_path = '/Users/petercorcoran/final_year_project/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 3) Function to fetch heatmap data for a given player & match
# ---------------------------------------------------------------------


def get_player_heatmap(match_id, player_id):
    """
    Fetches the heatmap JSON for a specific player in a specific match.
    """
    url = HEATMAP_URL_TEMPLATE.format(match_id=match_id, player_id=player_id)
    try:
        driver.get(url)

        # Wait until the <body> is present (adjust timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Parse the page source as JSON
        page_source = driver.find_element(By.TAG_NAME, "body").text
        data = json.loads(page_source)

        # The heatmap is typically found in data["heatmap"]
        heatmap = data.get('heatmap', [])
        return heatmap
    except Exception as e:
        print(f"Error fetching heatmap for match {
              match_id}, player {player_id}: {e}")
        return []

# ---------------------------------------------------------------------
# 4) Function to store heatmap in the appropriate "round_X" collection
# ---------------------------------------------------------------------


def store_player_heatmap_in_round_collection(round_number, match_id, player_id, heatmap_data):
    """
    Updates the round_X collection doc for this player & match with the heatmap.
    """
    round_collection_name = f"round_{round_number}"
    round_collection = db[round_collection_name]

    # Query to find the document
    update_query = {"_id": player_id, "match_id": match_id}

    # Data to update or insert
    update_data = {
        "$set": {
            "heatmap": heatmap_data,  # Add or update the heatmap field
        }
    }

    try:
        # Update or insert the document
        round_collection.update_one(update_query, update_data, upsert=True)
        print(
            f"Stored heatmap for player {player_id} in match {match_id}, "
            f"round {round_number} in collection {round_collection_name}."
        )
    except Exception as e:
        print(f"Error storing heatmap for player {player_id}: {e}")


# ---------------------------------------------------------------------
# 5) Fetch & store heatmaps for ALL matches & players
# ---------------------------------------------------------------------


def fetch_and_store_heatmaps_for_specific_rounds(rounds):
    """
    Fetch and store heatmaps only for matches in specific rounds.
    """
    all_matches = matches_collection.find({"roundInfo.round": {"$in": rounds}})

    for match in all_matches:
        match_id = match['_id']
        round_number = match['roundInfo']['round']

        home_team_id = match['homeTeam']['id']
        away_team_id = match['awayTeam']['id']

        # Fetch players for both teams
        home_players = db['players'].find({"team.id": home_team_id})
        away_players = db['players'].find({"team.id": away_team_id})

        # Process all players
        for player in list(home_players) + list(away_players):
            player_id = player.get('id', player['_id'])

            # Fetch heatmap data
            heatmap_data = get_player_heatmap(match_id, player_id)

            # Store in round collection
            store_player_heatmap_in_round_collection(
                round_number, match_id, player_id, heatmap_data
            )

        time.sleep(1)  # Small delay to prevent rate limiting




# ---------------------------------------------------------------------
# 6) Main Execution
# ---------------------------------------------------------------------
try:
    fetch_and_store_heatmaps_for_specific_rounds([23, 24, 25, 26, 27, 28, 29])()
finally:
    driver.quit()
