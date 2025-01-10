import pymongo
import requests
import time

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]
team_stats_collection = db["team_stats"]
teams_collection = db["teams"]

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept-Language": "en-US,en;q=0.5"
}

# Base URL for team statistics
base_url = "https://www.sofascore.com/api/v1/team/{team_id}/unique-tournament/17/season/61627/statistics/overall"


def fetch_team_stats(team_id):
    url = base_url.format(team_id=team_id)
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print(f"Successfully fetched data for team_id {team_id}")
            return response.json().get("statistics", {})
        else:
            print(f"Failed to fetch data for team_id {
                  team_id}. Status code: {response.status_code}")
            print(f"Response content: {response.content}")
            return None
    except Exception as e:
        print(f"Error fetching data for team_id {team_id}: {e}")
        return None

# Main function to fetch and store data for all teams


def fetch_and_store_team_stats():
    # Fetching only the _id of each team from the 'teams' collection
    team_ids = [str(team["_id"])
                for team in teams_collection.find({}, {"_id": 1})]

    for team_id in team_ids:
        stats = fetch_team_stats(team_id)
        if stats:
            team_stats_collection.update_one(
                {"team_id": team_id},
                {"$set": stats},
                upsert=True
            )
        time.sleep(1)  # Respectful delay

    print("Data fetch complete.")


# Run the function
fetch_and_store_team_stats()

# Close MongoDB connection
client.close()
