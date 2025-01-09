import pymongo
import pandas as pd
import time

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]

# List of all statistics fields to check (defined globally)
stats_fields = [
    "accurateCross", "accurateKeeperSweeper", "accurateLongBalls", "accuratePass",
    "aerialLost", "aerialWon", "bigChanceCreated", "bigChanceMissed",
    "blockedScoringAttempt", "challengeLost", "clearanceOffLine", "dispossessed",
    "duelLost", "duelWon", "errorLeadToAGoal", "errorLeadToAShot",
    "expectedAssists", "expectedGoals", "fouls", "goalAssist", "goals",
    "goalsPrevented", "goodHighClaim", "hitWoodwork", "interceptionWon",
    "keyPass", "lastManTackle", "minutesPlayed", "onTargetScoringAttempt",
    "outfielderBlock", "ownGoals", "penaltyConceded", "penaltyMiss",
    "penaltySave", "penaltyWon", "possessionLostCtrl", "punches",
    "savedShotsFromInsideTheBox", "saves", "shotOffTarget", "totalClearance",
    "totalContest", "totalCross", "totalKeeperSweeper", "totalLongBalls",
    "totalOffside", "totalPass", "totalTackle", "touches", "wasFouled", "wonContest"
]

# Main function to export all rounds into one CSV file


def export_all_rounds_to_csv(round_numbers, output_csv_file):
    # List to store all data across rounds
    all_data = []

    for round_number in round_numbers:
        collection_name = f"round_{round_number}"
        collection = db[collection_name]

        # Fetch all documents (each representing a player's statistics)
        documents = collection.find()

        # Process each document (player's stats)
        for doc in documents:
            player_id = doc["_id"]
            match_id = doc.get("match_id")

            # Create a row for each player's stats with match_id
            row = {"player_id": player_id, "match_id": match_id}

            # Add each statistic to the row, defaulting to 0 if not present
            for field in stats_fields:
                row[field] = doc.get(field, 0)

            # Append row to all_data
            all_data.append(row)

            # Slow down the process
            time.sleep(0.1)  # Adjust the delay as needed

    # Convert the accumulated data to a DataFrame
    df = pd.DataFrame(all_data)

    # Save to a single CSV file
    df.to_csv(output_csv_file, index=False, encoding='utf-8-sig')
    print(f"Exported all rounds stats to {output_csv_file}")

# Function to verify the data from MongoDB against the exported CSV


def verify_data(round_numbers, output_csv_file):
    # Read the data back from the CSV file
    df = pd.read_csv(output_csv_file)

    for round_number in round_numbers:
        collection_name = f"round_{round_number}"
        collection = db[collection_name]

        # Fetch all documents from MongoDB
        documents = collection.find()

        for doc in documents:
            player_id = doc["_id"]
            match_id = doc.get("match_id")

            # Find the corresponding row in the DataFrame
            csv_row = df[(df["player_id"] == player_id)
                         & (df["match_id"] == match_id)]

            if csv_row.empty:
                print(f"Error: No matching row found in CSV for player {
                      player_id} in match {match_id}")
                continue

            # Check each statistic field
            for field in stats_fields:
                mongo_value = doc.get(field, 0)
                csv_value = csv_row.iloc[0][field]

                if mongo_value != csv_value:
                    print(f"Mismatch in {field} for player {player_id} in match {
                          match_id}: MongoDB={mongo_value}, CSV={csv_value}")


# Export all rounds to one combined CSV file
output_csv_file = "all_rounds_player_stats.csv"
export_all_rounds_to_csv(range(1, 10), output_csv_file)

# Verify the data
verify_data(range(1, 10), output_csv_file)

# Close the MongoDB connection
client.close()
