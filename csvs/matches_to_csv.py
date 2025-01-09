import json
import csv
import datetime
import pymongo
import mysql.connector

# MongoDB connection details
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["soccer_db"]
matches_collection = db["matches"]

# MySQL connection details
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with your MySQL username
    password="root",  # Replace with your MySQL password
    database="premierleague"  # Replace with your MySQL database name
)

# Create a cursor to execute SQL queries
mysql_cursor = mysql_connection.cursor()

# Fetch teams and stadiums from MySQL
mysql_cursor.execute("SELECT team_id, stadium FROM Teams")
stadium_mapping = {team_id: stadium for team_id,
                   stadium in mysql_cursor.fetchall()}

# Specify the output CSV file name
output_csv_file = "matches.csv"

# Open the CSV file for writing
with open(output_csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)

    # Write the header
    writer.writerow([
        "match_id",
        "home_team_id",
        "away_team_id",
        "match_date",
        "stadium",
        "home_score",
        "away_score",
        "status"
    ])

    # Fetch matches from MongoDB
    matches = matches_collection.find()

    # Loop through each match and write to the CSV
    for match in matches:
        match_id = match["_id"]
        home_team_id = match["homeTeam"]["id"]
        away_team_id = match["awayTeam"]["id"]

        # Convert epoch time to a readable date format
        match_date = datetime.datetime.fromtimestamp(
            match["startTimestamp"]).strftime('%Y-%m-%d %H:%M:%S')

        # Get stadium name from the stadium mapping
        stadium = stadium_mapping.get(home_team_id, "Unknown Stadium")

        home_score = match.get("homeScore", {}).get("normaltime", None)
        away_score = match.get("awayScore", {}).get("normaltime", None)

        # Map status description to the desired status values
        status_description = match.get(
            "status", {}).get("description", "Unknown")
        if status_description == "Ended":
            status = "Completed"
        elif status_description == "Not started":
            status = "Upcoming"
        else:
            status = "Ongoing"  # or keep 'Unknown' if no clear mapping

        # Write the row to the CSV
        writer.writerow([
            match_id,
            home_team_id,
            away_team_id,
            match_date,
            stadium,
            home_score,
            away_score,
            status
        ])

# Close MySQL cursor and connection
mysql_cursor.close()
mysql_connection.close()

print(f"Data successfully written to {output_csv_file}.")
