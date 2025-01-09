from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt

# Connect to MongoDB (adjust with your connection settings)
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']  # Change to your database name

INITIAL_ELO = 1000  # Starting Elo for all players
K_FACTOR = 20  # The factor that determines Elo rating change

# Define weights for each statistic based on position
position_weights = {
    "GK": {  # Goalkeeper
        "accurateKeeperSweeper": 1, "goalsPrevented": 3, "saves": 2, "penaltySave": 5, "errorLeadToAGoal": -3, "punches": 1,
        "goodHighClaim": 2, "savedShotsFromInsideTheBox": 3, "totalClearance": 1, "totalContest": 0.5, "fouls": -1, "goals": -2
    },
    "DL": {  # Left-back
        "totalTackle": 2, "interceptionWon": 2, "aerialWon": 1.5, "dispossessed": -1, "clearanceOffLine": 4, "totalClearance": 2,
        "ownGoals": -5, "penaltyConceded": -3, "duelWon": 1.5, "fouls": -1, "totalCross": 1, "keyPass": 2, "bigChanceCreated": 3
    },
    "DR": {  # Right-back
        "totalTackle": 2, "interceptionWon": 2, "aerialWon": 1.5, "dispossessed": -1, "clearanceOffLine": 4, "totalClearance": 2,
        "ownGoals": -5, "penaltyConceded": -3, "duelWon": 1.5, "fouls": -1, "totalCross": 1, "keyPass": 2, "bigChanceCreated": 3
    },
    "DC": {  # Center-back
        "totalTackle": 2.5, "interceptionWon": 2, "aerialWon": 2.5, "dispossessed": -1, "clearanceOffLine": 5, "totalClearance": 3,
        "ownGoals": -5, "penaltyConceded": -3, "duelWon": 2, "fouls": -1, "blocks": 2, "lastManTackle": 4
    },
    "DM": {  # Defensive Midfielder
        "totalTackle": 2, "interceptionWon": 2, "duelWon": 2, "possessionLostCtrl": -1.5, "keyPass": 1.5, "totalPass": 1,
        "accuratePass": 2, "fouls": -1, "bigChanceCreated": 3, "totalLongBalls": 2, "penaltyConceded": -2
    },
    "MC": {  # Central Midfielder
        "totalTackle": 1.5, "interceptionWon": 1.5, "duelWon": 1.5, "possessionLostCtrl": -1.5, "keyPass": 2.5, "totalPass": 1,
        "accuratePass": 2, "expectedAssists": 2.5, "goalAssist": 3, "bigChanceCreated": 3, "totalLongBalls": 2
    },
    "ML": {  # Left Midfielder
        "totalTackle": 1, "interceptionWon": 1, "duelWon": 1.5, "accurateCross": 2, "keyPass": 3, "goalAssist": 3, "successfulDribbles": 2,
        "bigChanceCreated": 3, "expectedAssists": 2.5, "possessionLostCtrl": -1.5
    },
    "MR": {  # Right Midfielder
        "totalTackle": 1, "interceptionWon": 1, "duelWon": 1.5, "accurateCross": 2, "keyPass": 3, "goalAssist": 3, "successfulDribbles": 2,
        "bigChanceCreated": 3, "expectedAssists": 2.5, "possessionLostCtrl": -1.5
    },
    "AM": {  # Attacking Midfielder
        "keyPass": 3, "goalAssist": 3, "goals": 4, "onTargetScoringAttempt": 2, "bigChanceCreated": 3, "expectedAssists": 3,
        "possessionLostCtrl": -1, "totalPass": 1.5, "successfulDribbles": 2, "expectedGoals": 2
    },
    "LW": {  # Left Winger
        "goals": 4, "onTargetScoringAttempt": 2, "bigChanceCreated": 3, "keyPass": 3, "goalAssist": 2.5, "accurateCross": 2,
        "totalCross": 1.5, "successfulDribbles": 3, "expectedGoals": 2
    },
    "RW": {  # Right Winger
        "goals": 4, "onTargetScoringAttempt": 2, "bigChanceCreated": 3, "keyPass": 3, "goalAssist": 2.5, "accurateCross": 2,
        "totalCross": 1.5, "successfulDribbles": 3, "expectedGoals": 2
    },
    "ST": {  # Striker
        "goals": 5, "onTargetScoringAttempt": 2, "bigChanceMissed": -2, "expectedGoals": 2.5, "hitWoodwork": 1, "penaltyWon": 3,
        "penaltyMiss": -4, "goalAssist": 2.5, "wasFouled": 1
    }
}


def get_player_position(player_id):
    """Fetch the player's position from the players collection."""
    player = db['players'].find_one(
        {'_id': player_id})  # Use the correct key to match the player ID
    if player:
        return player.get('position')
    return None


def calculate_player_score(stats, position):
    """Calculate the player's performance score based on their statistics and position."""
    score = 0
    position_weight = position_weights.get(position)

    if not position_weight:
        return score  # No scoring if position weights are not defined

    for stat, weight in position_weight.items():
        score += stats.get(stat, 0) * weight

    return score


def update_elo(current_elo, actual_score, expected_score):
    """Update the player's Elo rating based on their actual performance vs expected."""
    return current_elo + K_FACTOR * (actual_score - expected_score)


def get_rounds_data(player_id, position, player_elo):
    """Gather statistics, calculate scores, and update Elo for the player across all rounds."""
    rounds_scores = []
    # Start with player's current Elo (default: 1000 if not set)
    current_elo = player_elo

    for round_number in range(1, 39):  # Assuming there are 38 rounds
        round_collection_name = f'round_{round_number}'

        if round_collection_name not in db.list_collection_names():
            continue  # Skip to the next round if this collection does not exist

        round_collection = db[round_collection_name]
        round_stats = round_collection.find()

        round_score = {
            "Round": round_number,
            "Score": 0,  # Total score for this round
            "Elo": current_elo,  # Elo before the match
        }

        for player_stats in round_stats:
            if player_stats.get('_id') == player_id:  # Match player_id
                # Calculate the actual performance score for this round
                actual_score = calculate_player_score(player_stats, position)

                # Use Elo to estimate the expected performance based on historical Elo rating
                # Normalize expected performance to 1
                expected_score = current_elo / INITIAL_ELO

                # Update the player's Elo rating based on actual vs expected performance
                current_elo = update_elo(
                    current_elo, actual_score, expected_score)

                # Store the updated Elo and actual performance score
                round_score["Score"] = actual_score
                round_score["Elo"] = current_elo

        if round_score["Score"] > 0:
            rounds_scores.append(round_score)

    return rounds_scores


def main():
    player_id = int(input("Enter Player ID: "))
    position = get_player_position(player_id)

    # Check if there's an existing Elo rating, else start with the initial Elo
    player_elo_record = db['elo_ratings'].find_one({"_id": player_id})
    player_elo = player_elo_record['elo'] if player_elo_record else INITIAL_ELO

    if position:
        print(f"Player Position: {position}")

        # Get round data and calculate Elo scores
        rounds_scores = get_rounds_data(player_id, position, player_elo)

        # Create a DataFrame for visualizing results
        df = pd.DataFrame(rounds_scores)

        # Print the DataFrame
        print(df)

        # Plot the Elo scores over the rounds
        plt.plot(df['Round'], df['Elo'], marker='o')
        plt.title(f'Elo Ratings for Player ID: {player_id} ({position})')
        plt.xlabel('Round')
        plt.ylabel('Elo Rating')
        plt.grid()
        plt.show()

    else:
        print("Player not found or position not available.")


if __name__ == "__main__":
    main()
