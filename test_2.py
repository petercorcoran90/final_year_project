from pymongo import MongoClient

# MongoDB setup (replace with your MongoDB URI if different)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']  # Replace with your database name

# Player ID to look for
player_id = 982780

# Function to iterate through each round collection and print goals for the given player ID


def print_player_goals(player_id):
    # Get all collections in the database that start with 'round_'
    collections = [col for col in db.list_collection_names()
                   if col.startswith('round_')]

    for collection_name in collections:
        collection = db[collection_name]
        # Find the player's document using their ID
        player_doc = collection.find_one({'_id': player_id})

        if player_doc:
            # Assuming goals are stored under 'goals' in the player's document
            goals = player_doc.get('goals', 0)
            print(f"Collection: {collection_name} | Goals: {goals}")
        else:
            print(f"Collection: {
                  collection_name} | No data for player {player_id}")


# Run the function to print player goals
print_player_goals(player_id)
