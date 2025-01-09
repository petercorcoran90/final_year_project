import requests
from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['football_db']
teams_collection = db['teams']
players_collection = db['players']

# Function to fetch and insert players for each team


def fetch_and_insert_players(team_id):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/players"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Loop through players and insert into MongoDB
        for player_info in data['players']:
            player = player_info['player']  # Access the nested player data

            # Set the player's API 'id' as MongoDB '_id'
            # Assign player id from API as the MongoDB _id
            player['_id'] = player['id']

            # Optionally, if you need to add the team_id
            # player['team_id'] = team_id  # Uncomment this if you want to add team_id

            try:
                # Insert player into MongoDB collection, if player doesn't exist already
                players_collection.insert_one(player)
                print(f"Inserted player {
                      player['name']} with id {player['_id']}.")
            except Exception as e:
                print(f"An error occurred inserting player {
                      player['name']} (id {player['_id']}): {e}")
    else:
        print(f"Failed to fetch players for team {
              team_id}: Status code {response.status_code}")


# Fetch all team IDs from the teams collection
team_ids = teams_collection.distinct('_id')  # Assuming _id stores the team_id

# Loop over each team and fetch players
for team_id in team_ids:
    fetch_and_insert_players(team_id)

# Close the MongoDB connection
client.close()
