from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]

# Test query
player_id = 922573  # Example player ID
player_data = db.players.find_one({"_id": player_id})

if player_data:
    print("Player data retrieved successfully:")
    print(player_data)
else:
    print(f"No player found with ID {player_id}")
