import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['football_db']
# Replace with your actual teams collection name
teams_collection = db['teams']
# Replace with your actual players collection name
players_collection = db['players']


def fetch_teams_and_players():
    # Initialize an empty list to hold team and player data
    data = []

    # Fetch all teams
    teams = teams_collection.find()  # Adjust your query as necessary

    for team in teams:
        team_id = team['_id']  # Assuming team ID is stored in '_id'
        # Adjust if team name is stored differently
        team_name = team.get('name')

        # Fetch players associated with the team
        players = players_collection.find({'team.id': team_id})

        # Collect player names
        player_names = [player['name'] for player in players]

        # Append the team and player names to the data list
        data.append({'Team': team_name, 'Players': player_names})

    # Create a DataFrame from the collected data
    df = pd.DataFrame(data)
    return df


# Fetch the data and display it
teams_df = fetch_teams_and_players()
print(teams_df)

# Optional: To visualize it nicely, you can display it in Jupyter Notebook with the following:
# display(teams_df)
