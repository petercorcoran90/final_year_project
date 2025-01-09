import time
import json
from pymongo import MongoClient

# ----- [ Selenium Imports ] -----
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# MongoDB setup (replace with your MongoDB URI if different)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
matches_collection = db['matches']  # Collection to store matches
# Assuming teams are stored in this collection
teams_collection = db['teams']

# Base URL and Premier League details
TEAM_EVENTS_URL = "https://api.sofascore.com/api/v1/team/{team_id}/events/next/0"
LEAGUE_ID = 17   # Premier League ID
SEASON_ID = 61627  # Current Premier League season ID

# ---------------------------------------------------------------------
# 1) Setup Selenium WebDriver
# ---------------------------------------------------------------------
# Adjust this path to your local ChromeDriver
driver_path = '/Users/petercorcoran/python/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 2) Function to get teams (unchanged)
# ---------------------------------------------------------------------


def get_teams():
    """
    Fetches team documents from MongoDB.
    Assuming you've already fetched the teams from the Premier League
    and stored them in this collection.
    """
    return teams_collection.find({}, {'_id': 1})  # Only return team IDs

# ---------------------------------------------------------------------
# 3) Function to get team matches using Selenium instead of requests
# ---------------------------------------------------------------------


def get_team_matches(team_id):
    """
    Navigates to the Sofascore events URL for the given team_id in Chrome
    and extracts the JSON data from the page source.
    """
    url = TEAM_EVENTS_URL.format(team_id=team_id)
    try:
        # Go to the URL with Selenium
        driver.get(url)

        # Wait until the page body is present (adjust timeout/conditions as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract the raw text from the page body
        page_source = driver.find_element(By.TAG_NAME, "body").text

        # Parse the text as JSON
        response_data = json.loads(page_source)

        # Extract the matches from the 'events' field
        team_matches = response_data.get('events', [])
        print(f"Fetched {len(team_matches)} matches for team {team_id}")
        return team_matches
    except Exception as e:
        print(f"Error fetching matches for team {team_id}: {e}")
        return []

# ---------------------------------------------------------------------
# 4) Function to filter matches to Premier League & current season (unchanged)
# ---------------------------------------------------------------------


def filter_premier_league_matches(matches):
    filtered_matches = []
    for match in matches:
        # Ensure the 'tournament' and 'season' fields exist in the match data
        if 'tournament' in match and 'season' in match:
            tournament = match['tournament']
            season_id = match['season']['id']

            # Check if 'uniqueTournament' exists in the 'tournament' object
            if 'uniqueTournament' in tournament:
                unique_tournament_id = tournament['uniqueTournament']['id']
                print(
                    f"Checking match with uniqueTournament ID: {
                        unique_tournament_id}, Season ID: {season_id}"
                )

                # Filter for Premier League and current season matches
                if unique_tournament_id == LEAGUE_ID and season_id == SEASON_ID:
                    print(
                        "Match belongs to Premier League 24/25, adding to filtered matches")
                    filtered_matches.append(match)
                else:
                    print("Match does not belong to Premier League 24/25, skipping")
            else:
                print(
                    f"'uniqueTournament' field missing in 'tournament' for match ID: {
                        match.get('id', 'unknown')}, skipping"
                )
        else:
            print(
                f"'tournament' or 'season' fields missing for match ID: {
                    match.get('id', 'unknown')}, skipping"
            )

    print(f"Filtered {len(filtered_matches)} Premier League matches")
    return filtered_matches

# ---------------------------------------------------------------------
# 5) Function to store matches in MongoDB (unchanged)
# ---------------------------------------------------------------------


def store_matches_in_mongodb(matches):
    for match in matches:
        match_data = match.copy()  # Create a copy of the match data

        # Set a unique identifier for the match using its ID
        match_data['_id'] = match_data.pop('id')

        # Check if the match already exists in the MongoDB collection
        if not matches_collection.find_one({'_id': match_data['_id']}):
            # Insert the match into MongoDB if it doesn't exist
            matches_collection.insert_one(match_data)
            print(
                f"Stored match: {match_data['homeTeam']['name']} vs {
                    match_data['awayTeam']['name']} "
                f"on {match_data['startTimestamp']}"
            )
        else:
            print(
                f"Match {match_data['homeTeam']['name']} vs {
                    match_data['awayTeam']['name']} already exists in the database."
            )

# ---------------------------------------------------------------------
# 6) Main function to fetch and store Premier League matches
# ---------------------------------------------------------------------


def fetch_and_store_premier_league_matches():
    teams = get_teams()

    for team in teams:
        team_id = team['_id']
        print(f"Fetching matches for team {team_id}...")

        # Get matches for the current team using Selenium
        team_matches = get_team_matches(team_id)

        # Filter matches to only include Premier League matches from the current season
        premier_league_matches = filter_premier_league_matches(team_matches)

        # Store the filtered matches in MongoDB
        store_matches_in_mongodb(premier_league_matches)

        # Add a small delay to reduce any potential rate-limiting or page-load issues
        time.sleep(2)


# ---------------------------------------------------------------------
# 7) Execute the function and close the browser
# ---------------------------------------------------------------------
try:
    fetch_and_store_premier_league_matches()
finally:
    # Be sure to close the browser at the end
    driver.quit()
