import csv
import pymongo
from datetime import datetime

# MongoDB connection setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]
players_collection = db["players"]

# CSV headers
csv_headers = [
    "player_id", "team_id", "player_name", "position",
    "nationality", "date_of_birth", "height", "market_value"
]

# Convert timestamp to date


def convert_timestamp_to_date(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else None


# Fetch all player documents from MongoDB
player_documents = players_collection.find({})

# Prepare data for CSV
csv_data = []
for player in player_documents:
    csv_data.append({
        "player_id": player.get("_id"),
        "team_id": player["team"].get("id"),
        "player_name": player.get("name"),
        "position": player.get("position"),
        "nationality": player["country"].get("name"),
        "date_of_birth": convert_timestamp_to_date(player.get("dateOfBirthTimestamp")),
        "height": player.get("height"),
        "market_value": player.get("proposedMarketValue")
    })

# Write data to CSV with utf-8-sig encoding
with open("players.csv", mode="w", newline="", encoding="utf-8-sig") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
    writer.writeheader()
    writer.writerows(csv_data)

print("CSV file 'players.csv' has been created with utf-8-sig encoding.")
