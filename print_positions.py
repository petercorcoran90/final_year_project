from pymongo import MongoClient

# 1. Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']

# 2. Reference the players collection
players_collection = db['players']

# 3. Create a set to hold unique positions
unique_positions = set()

# 4. Iterate over all players
for player in players_collection.find():
    # If "positions" is a list of position strings, collect them
    if "positions" in player:
        for pos in player["positions"]:
            unique_positions.add(pos)

    # If some players might only have a single "position" field (string), handle that too:
    if "position" in player and isinstance(player["position"], str):
        unique_positions.add(player["position"])

# 5. Print all distinct positions found
print("All distinct positions in the database:")
for position in sorted(unique_positions):
    print(position)
