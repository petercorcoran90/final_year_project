import requests
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['football_db']
players_collection = db['players']
statistics_collection = db['statistics']

# Function to fetch and insert player statistics


def fetch_and_insert_player_statistics(player_id, player_name):
    url = f"https://api.sofascore.com/api/v1/player/{
        player_id}/unique-tournament/17/season/61627/statistics/overall"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Prepare the statistics data
        statistics_data = {
            "_id": player_id,  # Use player ID as the document ID
            "statistics": data['statistics']
        }

        # Check if the player's statistics already exist in the database
        existing_stats = statistics_collection.find_one({"_id": player_id})

        if existing_stats:
            # If statistics exist, check if they are different
            if existing_stats['statistics'] != statistics_data['statistics']:
                # Update the statistics and print a message
                statistics_collection.replace_one(
                    {"_id": player_id}, statistics_data)
                print(f"Statistics updated for {
                      player_name} (ID: {player_id})")
            else:
                print(f"No changes in statistics for {
                      player_name} (ID: {player_id})")
        else:
            # Insert new statistics if they don't exist
            statistics_collection.insert_one(statistics_data)
            print(f"Statistics inserted for {player_name} (ID: {player_id})")
    else:
        print(f"Failed to fetch data for {player_name} (ID: {player_id})")

# Function to fetch statistics for all players


def fetch_statistics_for_all_players():
    # Fetch all players from the players collection
    players = players_collection.find()

    for player in players:
        player_id = player['_id']  # Assuming player ID is stored as '_id'
        # Assuming player name is stored as 'name'
        player_name = player['name']
        fetch_and_insert_player_statistics(player_id, player_name)


# Example usage
fetch_statistics_for_all_players()
