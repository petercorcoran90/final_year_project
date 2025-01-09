import requests
from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['football_db']
collection = db['teams']

# URL endpoint
url = "https://www.sofascore.com/api/v1/unique-tournament/17/season/61627/teams"

# Fetching data from the API
response = requests.get(url)
data = response.json()

# Inserting teams into MongoDB with custom _id using team_id
if 'teams' in data:
    teams_data = data['teams']

    for team in teams_data:
        # Assuming 'team_id' is present in the API data
        if 'id' in team:
            team['_id'] = team['id']  # Assign the 'team_id' to MongoDB's '_id'

    try:
        # Insert all teams into the collection
        collection.insert_many(teams_data, ordered=False)
        print(f"Inserted {len(teams_data)} teams into the database.")
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("Invalid data structure from API response.")

# Close the MongoDB connection
client.close()
