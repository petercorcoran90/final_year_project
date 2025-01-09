import requests
import mysql.connector
from mysql.connector import Error

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'premier_league_db'
}

# List of teams and their IDs
teams = {
    42: 'Arsenal',
    31: 'Leicester City',
    30: 'Brighton & Hove Albion',
    50: 'Brentford',
    60: 'Bournemouth',
    40: 'Aston Villa',
    14: 'Nottingham Forest',
    3: 'Wolverhampton',
    43: 'Fulham',
    17: 'Manchester City',
    37: 'West Ham United',
    32: 'Ipswich Town',
    33: 'Tottenham Hotspur',
    7: 'Crystal Palace',
    35: 'Manchester United',
    45: 'Southampton',
    38: 'Chelsea',
    48: 'Everton',
    39: 'Newcastle United',
    44: 'Liverpool'
}

# API base URL
api_base_url = 'https://www.sofascore.com/api/v1/team/{team_id}/unique-tournament/17/season/61627/statistics/overall'

# Function to fetch data from API and insert into MySQL


def fetch_and_insert_team_stats(team_id, team_name):
    response = requests.get(api_base_url.format(team_id=team_id))

    if response.status_code == 200:
        data = response.json()

        # Extract necessary fields from the JSON response
        matches_played = data['statistics']['matchesPlayed']
        wins = data['statistics']['wins']
        draws = data['statistics']['draws']
        losses = data['statistics']['losses']
        goals_scored = data['statistics']['goalsFor']
        goals_conceded = data['statistics']['goalsAgainst']
        points = data['statistics']['points']

        try:
            # Connect to the database
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # SQL query to insert data into Team_Stats table
            insert_query = """
            INSERT INTO Team_Stats (team_id, season, matches_played, wins, draws, losses, goals_scored, goals_conceded, points)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            season = '2023-2024'  # Adjust the season as needed
            cursor.execute(insert_query, (team_id, season, matches_played,
                           wins, draws, losses, goals_scored, goals_conceded, points))

            # Commit transaction
            connection.commit()

            print(f"Data for {team_name} inserted successfully!")

        except Error as e:
            print(f"Error: {e}")

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        print(f"Failed to fetch data for {
              team_name}, status code: {response.status_code}")


# Iterate through teams and fetch/insert data
for team_id, team_name in teams.items():
    fetch_and_insert_team_stats(team_id, team_name)
