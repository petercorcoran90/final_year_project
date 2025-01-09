import csv
from pymongo import MongoClient

# MongoDB setup (replace with your MongoDB URI if different)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
teams_collection = db['teams']  # Collection to store team data

# Output CSV file path
output_file = "teams_export.csv"


def export_teams_to_csv():
    # Define the headers for the CSV
    headers = ["team_id", "team_name", "city",
               "stadium", "founded_year", "manager"]

    # Open the file in write mode
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write the header row
        writer.writeheader()

        # Fetch all documents from the teams collection
        for team in teams_collection.find():
            # Map MongoDB fields to CSV columns
            team_data = {
                "team_id": team["_id"],
                "team_name": team.get("name", ""),
                "city": team.get("city", ""),
                "stadium": team.get("stadium", ""),
                "founded_year": team.get("founded_year", ""),
                "manager": team.get("manager", "")
            }

            # Write the team data as a row in the CSV
            writer.writerow(team_data)
            print(f"Exported team: {team_data['team_name']}")

    print(f"Export completed. Data saved to {output_file}")


# Execute the function to export teams to CSV
export_teams_to_csv()
