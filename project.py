import requests
from pymongo import MongoClient

# MongoDB setup (replace with your MongoDB URI if different)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
teams_collection = db['teams']  # Collection to store teams

# Base URLs
BASE_TOURNAMENT_URL = "https://www.sofascore.com/api/v1/unique-tournament"

# Premier League and current season details
LEAGUE_ID = 17  # Premier League ID
SEASON_ID = 61627  # Current Premier League season ID


def get_teams_in_current_season():
    url = f"{BASE_TOURNAMENT_URL}/{LEAGUE_ID}/season/{SEASON_ID}/teams"
    response = requests.get(url)

    if response.status_code == 200:
        teams_data = response.json()['teams']
        return teams_data
    else:
        print(f"Error fetching teams: {response.status_code}")
        return []

# Fetch and store teams in MongoDB with custom _id


def store_teams_in_mongodb():
    teams = get_teams_in_current_season()

    if teams:
        for team in teams:
            team_data = team.copy()  # Create a copy of the team data

            # Set the 'id' as the MongoDB '_id'
            # Use the 'id' as the MongoDB '_id'
            team_data['_id'] = team_data.pop('id')

            # Check if the team already exists in the MongoDB collection
            if not teams_collection.find_one({'_id': team_data['_id']}):
                # Insert the team into MongoDB if it doesn't exist
                teams_collection.insert_one(team_data)
                print(f"Stored team: {team_data['name']}")
            else:
                print(f"Team {team_data['name']
                              } already exists in the database.")
    else:
        print("No teams to store.")


# Execute the function to store teams in MongoDB
store_teams_in_mongodb()
