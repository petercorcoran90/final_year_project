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
# Collection where matches are stored
matches_collection = db['matches']
# Collection for match statistics
match_statistics_collection = db['match_statistics']

# API URL to get match statistics
MATCH_STATISTICS_URL = "https://api.sofascore.com/api/v1/event/{match_id}/statistics"

# ---------------------------------------------------------------------
# 1) Setup Selenium WebDriver
# ---------------------------------------------------------------------
# Adjust this path to your local ChromeDriver
driver_path = '/Users/petercorcoran/final_year_project/chromedriver'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ---------------------------------------------------------------------
# 2) Function to fetch match statistics using Selenium
# ---------------------------------------------------------------------


def get_match_statistics(match_id):
    """
    Navigates to the Sofascore match statistics API endpoint in Chrome
    and returns the match statistics as JSON data.
    """
    url = MATCH_STATISTICS_URL.format(match_id=match_id)
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

        # Extract the statistics from the JSON
        statistics = response_data.get('statistics', {})
        print(f"Fetched statistics for match ID {match_id}")
        return statistics
    except Exception as e:
        print(f"Error fetching statistics for match ID {match_id}: {e}")
        return None

# ---------------------------------------------------------------------
# 3) Function to store match statistics in MongoDB (unchanged)
# ---------------------------------------------------------------------


def store_match_statistics(match_id, statistics):
    """
    Store match statistics in MongoDB with match_id as the unique identifier.
    """
    if statistics:
        # Prepare the document with match_id as the _id to ensure uniqueness
        statistics_data = {
            '_id': match_id,
            'statistics': statistics
        }

        # Check if the match statistics already exist in the database
        if not match_statistics_collection.find_one({'_id': match_id}):
            match_statistics_collection.insert_one(statistics_data)
            print(f"Stored statistics for match ID {match_id}")
        else:
            print(f"Statistics for match ID {
                  match_id} already exist in the database.")
    else:
        print(f"No statistics to store for match ID {match_id}")

# ---------------------------------------------------------------------
# 4) Main function to fetch and store match statistics for rounds 21 and 22
# ---------------------------------------------------------------------


def fetch_and_store_match_statistics_for_specific_rounds(rounds):
    """
    Fetch statistics for matches in specific rounds and store them in match_statistics.
    """
    # Filter matches for the specific rounds
    matches = matches_collection.find(
        {"roundInfo.round": {"$in": rounds}}, {'_id': 1})

    for match in matches:
        match_id = match['_id']
        print(f"Fetching statistics for match ID {match_id}...")

        # Fetch statistics for the current match via Selenium
        statistics = get_match_statistics(match_id)

        # Store the statistics in MongoDB
        store_match_statistics(match_id, statistics)

        # Add a small delay if desired to reduce any potential rate-limiting or page-load issues
        time.sleep(1)


# ---------------------------------------------------------------------
# 5) Execute the function for rounds 21 and 22 and close the browser
# ---------------------------------------------------------------------
try:
    fetch_and_store_match_statistics_for_specific_rounds([23, 24, 25, 26, 27, 28, 29])
finally:
    # Be sure to close the browser at the end
    driver.quit()
