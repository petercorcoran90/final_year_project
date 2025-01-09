import requests
import pandas as pd

# The URL you want to get data from
url = "https://www.sofascore.com/api/v1/event/11911622/shotmap"

# Send a GET request to the API
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Print the data or work with it
    # Extract relevant information from each entry in 'shotmap'
    shot_data = []
    for shot in data['shotmap']:
        player = shot['player']
        shot_data.append({
            'Player Name': player['name'],
            'Player Short Name': player['shortName'],
            'Player Position': player['position'],
            'Is Home Team': shot['isHome'],
            'Shot Type': shot.get('shotType'),
            'Goal Type': shot.get('goalType', None),
            'Situation': shot.get('situation', None),
            'Body Part': shot.get('bodyPart', None),
            'Goal Mouth Location': shot.get('goalMouthLocation', None),
            'XG': shot.get('xg'),
            'XG on Target': shot.get('xgot', None),
            'Time (min)': shot.get('time'),
            'Added Time (min)': shot.get('addedTime', 0),
            'Incident Type': shot.get('incidentType'),
            'Coordinates X': shot['playerCoordinates'].get('x'),
            'Coordinates Y': shot['playerCoordinates'].get('y'),
            'Coordinates Z': shot['playerCoordinates'].get('z')
        })

    # Create DataFrame
    df = pd.DataFrame(shot_data)

    # Display DataFrame
    print(df)

else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
