import requests
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
players_collection = db['players']  # Collection storing player information

# Function to fetch player information from the API


def fetch_player_info(player_id):
    url = f"https://api.sofascore.com/api/v1/player/{player_id}/"
    print(f"Fetching data for player ID: {player_id}")
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()  # Parse the JSON response
    else:
        print(f"Failed to fetch player data for ID {
              player_id}: {response.status_code}")
        return None

# Function to update player information in MongoDB


def update_player_info():
    # Get all player IDs (_id) from the MongoDB collection
    player_ids = players_collection.distinct('_id')

    for player_id in player_ids:
        player_data = fetch_player_info(player_id)

        if player_data and 'player' in player_data:  # Ensure the response contains player data
            player_document = player_data['player']
            player_document['_id'] = player_document.pop(
                'id')  # Ensure '_id' is set

            try:
                players_collection.replace_one(
                    {'_id': player_document['_id']}, player_document, upsert=True
                )
                print(f"Updated player data for ID {player_document['_id']}")
            except Exception as e:
                print(f"Error updating data for player ID {
                      player_document['_id']}: {e}")
        else:
            print(f"No valid data found for player ID: {player_id}")


# Execute the function to update all players
update_player_info()
