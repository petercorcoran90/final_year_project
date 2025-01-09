import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['football_db']
players_collection = db['players']
statistics_collection = db['statistics']

# Function to get top 10 players based on a specified statistic


def get_top_players_by_statistic(statistic):
    # Fetch all statistics documents
    statistics_data = list(statistics_collection.find({}))

    # Create a list to hold player details
    players_stats = []

    # Loop through statistics to extract player ID, team, and the specified statistic
    for stat in statistics_data:
        player_id = stat['_id']
        player_stats = stat['statistics']

        # Get the statistic value (default to 0 if not present)
        value = player_stats.get(statistic, 0)

        # Find player information in the players collection
        player = players_collection.find_one({"_id": player_id})

        if player:
            player_name = player['name']
            team_name = player['team']['name'] if 'team' in player else "Unknown"
            players_stats.append({
                'player_name': player_name,
                'team_name': team_name,
                'value': value
            })

    # Create a DataFrame for easier sorting and viewing
    players_df = pd.DataFrame(players_stats)

    # Sort by the specified statistic value and get top 10 players
    top_players_df = players_df.sort_values(
        by='value', ascending=False).head(10)

    return top_players_df


# Get user input for the statistic to search
statistic_input = input(
    "Enter the statistic to search (e.g., interceptions, goals, assists): ")

# Get top 10 players for the specified statistic
top_players_df = get_top_players_by_statistic(statistic_input)

# Print the results
if not top_players_df.empty:
    print(f"Top 10 players for '{statistic_input}':")
    print(top_players_df.to_string(index=False))
else:
    print(f"No players found for the statistic '{statistic_input}'.")
