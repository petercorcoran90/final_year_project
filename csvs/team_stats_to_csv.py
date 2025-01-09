import requests
import csv

# Define the API endpoint
url = "https://www.sofascore.com/api/v1/tournament/1/season/61627/standings/total"

# Send a request to the API
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Prepare the data for CSV
    standings = data.get("standings", [])
    rows = []

    for standing in standings:
        for row in standing.get("rows", []):
            team = row.get("team", {})
            matches_played = row.get("matches", 0)
            wins = row.get("wins", 0)
            draws = row.get("draws", 0)
            losses = row.get("losses", 0)
            goals_scored = row.get("scoresFor", 0)
            goals_conceded = row.get("scoresAgainst", 0)
            team_id = team.get("id", None)

            # Append the row to the list
            rows.append([
                None,  # team_stat_id (can be NULL)
                team_id,
                matches_played,
                wins,
                draws,
                losses,
                goals_scored,
                goals_conceded
            ])

    # Define CSV file name
    csv_file_name = "standings.csv"

    # Write the data to CSV
    with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["team_stat_id", "team_id", "matches",
                        "wins", "draws", "losses", "scoresFor", "scoresAgainst"])
        # Write the data rows
        writer.writerows(rows)

    print(f"Data has been successfully written to {csv_file_name}")
else:
    print(f"Failed to fetch data from API. Status code: {
          response.status_code}")
