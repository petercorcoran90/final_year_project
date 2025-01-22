from pymongo import MongoClient

# 1) Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]
players_collection = db["players"]


def remove_old_position_field():
    """
    Find all players that still have the 'position' field
    and remove it, leaving only the 'positions' array.
    """
    # Query to match documents that have a 'position' field
    query = {"position": {"$exists": True}}

    # Find all matching players
    players = players_collection.find(query)

    count = 0
    for player in players:
        player_id = player["_id"]
        # Remove the 'position' field
        result = players_collection.update_one(
            {"_id": player_id},
            {"$unset": {"position": ""}}  # $unset removes a field
        )

        if result.modified_count > 0:
            print(f"Removed old 'position' field from player _id={player_id}")
            count += 1

    print(f"\nDone. Removed 'position' from {count} players.")


def main():
    remove_old_position_field()


if __name__ == "__main__":
    main()
