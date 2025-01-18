import pandas as pd
import numpy as np
from pymongo import MongoClient

# ------------------------------------------------
# 1) Connect to MongoDB
# ------------------------------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]  # Replace with your DB name

# ------------------------------------------------
# 2) Load Round Stats (round_1 .. round_20)
# ------------------------------------------------
all_round_dfs = []
for i in range(1, 21):
    round_name = f"round_{i}"
    docs = list(db[round_name].find({}))
    df = pd.DataFrame(docs)
    df["round"] = i
    all_round_dfs.append(df)

round_stats_df = pd.concat(all_round_dfs, ignore_index=True)
print("round_stats_df columns:", round_stats_df.columns)
print(round_stats_df.head())

# ------------------------------------------------
# 3) Load Players
#    In your schema, 'players' has _id = player_id, and round_X also uses _id = player_id.
# ------------------------------------------------
players_docs = list(db["players"].find({}))
players_df = pd.DataFrame(players_docs)
print("players_df columns:", players_df.columns)
print(players_df.head())

# ------------------------------------------------
# 4) Merge Round Stats with Player Info on '_id'
#    So each row = (player, match) from round_stats_df plus player details from players_df.
# ------------------------------------------------
# If *both* round_stats_df and players_df use _id for player ID, no rename is needed.
# Make sure your round_stats_df does not have a separate column like 'player_id' conflicting.
# If you see columns like 'player_id' in round_stats_df, you may want to drop or rename them.

merged_player_stats_df = pd.merge(
    round_stats_df,
    players_df,
    on="_id",      # merging on the _id field (the same in both)
    how="left"     # or 'inner' if you only want players actually in round_stats
)
print("merged_player_stats_df columns:", merged_player_stats_df.columns)
print(merged_player_stats_df.head())

# ------------------------------------------------
# 5) Load Matches, Merge on 'match_id'
# ------------------------------------------------
matches_docs = list(db["matches"].find({}))
matches_df = pd.DataFrame(matches_docs)

# We'll rename the '_id' in matches_df to 'match_id' so we can merge on a single field
matches_df.rename(columns={"_id": "match_id"}, inplace=True)

final_df = pd.merge(
    merged_player_stats_df,
    matches_df,
    on="match_id",  # now both dataframes have 'match_id'
    how="left"
)
print("final_df columns:", final_df.columns)
print(final_df.head())

# ------------------------------------------------
# 6) Load match_stats (has nested "statistics"), flatten the "ALL" period
# ------------------------------------------------
match_stats_docs = list(db["match_statistics"].find({}))


def parse_all_period_stats(doc):
    # We only parse period="ALL".
    match_id_val = doc["_id"]
    stats_array = doc.get("statistics", [])

    # Look for the object with period="ALL"
    all_period_obj = next(
        (p for p in stats_array if p["period"] == "ALL"), None)
    flattened = {"match_id": match_id_val}

    if not all_period_obj:
        # If there's no "ALL" period, just return {"match_id": ...}
        return flattened

    # all_period_obj["groups"] is a list of groups, each with "statisticsItems"
    for group in all_period_obj["groups"]:
        for item in group["statisticsItems"]:
            key = item.get("key")  # e.g. "ballPossession", "expectedGoals"
            home_val = item.get("homeValue")
            away_val = item.get("awayValue")
            if key:
                # We'll create columns like 'ballPossession_home', 'ballPossession_away'
                flattened[f"{key}_home"] = home_val
                flattened[f"{key}_away"] = away_val

    return flattened


rows = []
for doc in match_stats_docs:
    row_dict = parse_all_period_stats(doc)
    rows.append(row_dict)

parsed_stats_df = pd.DataFrame(rows)
# Now parsed_stats_df has columns like 'match_id', 'ballPossession_home', 'ballPossession_away', etc.

print("parsed_stats_df columns:", parsed_stats_df.columns)
print(parsed_stats_df.head())

# 7) Merge flattened match stats with final_df
#    Now each (player, match) row can have e.g. 'ballPossession_home' if available.
#    But we must ensure 'parsed_stats_df' is not empty AND has 'match_id' column
if not parsed_stats_df.empty and "match_id" in parsed_stats_df.columns:
    final_df_with_stats = pd.merge(
        final_df,
        parsed_stats_df,    # flattened ALL period stats
        on="match_id",
        how="left"
    )
else:
    print("No valid match_id in parsed_stats_df (or it's empty). Skipping merge.")
    final_df_with_stats = final_df

print("final_df_with_stats columns:", final_df_with_stats.columns)
print(final_df_with_stats.head())

# ------------------------------------------------
# 8) Keep a row per (player, match)
#    (No grouping, so no groupby)
# ------------------------------------------------

# ------------------------------------------------
# 9) Clean & Drop Unneeded Columns
# ------------------------------------------------
columns_to_drop = [
    "ratingVersions",
    "player_id",
    "firstName",
    "lastName",
    "slug_x",
    "shortName",
    "retired",
    "userCount",
    "gender",
    "shirtNumber",
    "fieldTranslations",
    "deceased",
    "customId",
    "status",
    "winnerCode",
    "changes",
    "hasGlobalHighlights",
    "hasXg",
    "hasEventPlayerStatistics",
    "hasEventPlayerHeatMap",
    "detailId",
    "crowdsourcingDataDisplayEnabled",
    "startTimestamp",
    "slug_y",
    "finalResultOnly",
    "feedLocked",
    "isEditor",
    "roundInfo"
]

final_df_with_stats.drop(columns=columns_to_drop,
                         inplace=True, errors="ignore")


def clean_data(df):
    # 1. Extracting card details (yellow/red and time)
    def extract_card_info(cards):
        if isinstance(cards, list) and len(cards) > 0:
            return f"{cards[0].get('incidentClass', 'N/A')}-{cards[0].get('time', 'N/A')}"
        return 'No Card'

    # 2. Extracting team name or ID
    def extract_team_info(team):
        if isinstance(team, dict):
            # Change to 'id' if you prefer team ID
            return team.get('name', 'Unknown')
        return 'Unknown'

    # 3. Extract country 3-letter code
    def extract_country(country):
        if isinstance(country, dict):
            return country.get('alpha3', 'N/A')
        return 'N/A'

    # 4. Extract tournament ID
    def extract_tournament(tournament):
        if isinstance(tournament, dict):
            return tournament.get('uniqueTournament', {}).get('id', 'N/A')
        return 'N/A'

    # 5. Extract season ID
    def extract_season(season):
        if isinstance(season, dict):
            return season.get('id', 'N/A')
        return 'N/A'

    def extract_normaltime_score(score):
        if isinstance(score, dict):
            return score.get('normaltime', 0)
        return 0

    def extract_team_id(team):
        if isinstance(team, dict):
            return team.get('id', 'Unknown')
        return 'Unknown'

    # Apply transformations
    df['card_info'] = df['cards'].apply(extract_card_info)
    df['team_name'] = df['team'].apply(extract_team_info)
    df['country_code'] = df['country'].apply(extract_country)
    df['tournament_id'] = df['tournament'].apply(extract_tournament)
    df['season_id'] = df['season'].apply(extract_season)
    df['home_team_id'] = df['homeTeam'].apply(extract_team_id)
    df['away_team_id'] = df['awayTeam'].apply(extract_team_id)
    df['home_score'] = df['homeScore'].apply(extract_normaltime_score)
    df['away_score'] = df['awayScore'].apply(extract_normaltime_score)

    # Drop redundant columns after extracting values
    columns_to_drop = [
        'cards', 'team', 'country', 'proposedMarketValueRaw', 'tournament', 'season',
        'homeTeam', 'awayTeam', 'homeScore', 'awayScore', 'time'
    ]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')
    return df


# Apply the cleaning function to the dataframe
final_df_with_stats = clean_data(final_df_with_stats)

# Replace NaN or None values with 0 in the entire dataframe
final_df_with_stats = final_df_with_stats.fillna(0)

# Replace empty arrays or strings with 0 for specific columns like 'heatmap'


def replace_empty_with_zero(value):
    if isinstance(value, list) and len(value) == 0:  # Empty list
        return 0
    if isinstance(value, str) and value.strip() == "":  # Empty string
        return 0
    return value


# Function to process heatmap data into numerical features
def process_heatmap(heatmap):
    if isinstance(heatmap, list) and len(heatmap) > 0:
        x_coords = [point['x'] for point in heatmap if isinstance(point, dict)]
        y_coords = [point['y'] for point in heatmap if isinstance(point, dict)]
        return {
            "heatmap_count": len(heatmap),
            "heatmap_avg_x": sum(x_coords) / len(x_coords) if x_coords else 0,
            "heatmap_avg_y": sum(y_coords) / len(y_coords) if y_coords else 0,
            "heatmap_var_x": np.var(x_coords) if x_coords else 0,
            "heatmap_var_y": np.var(y_coords) if y_coords else 0,
        }
    return {"heatmap_count": 0, "heatmap_avg_x": 0, "heatmap_avg_y": 0, "heatmap_var_x": 0, "heatmap_var_y": 0}


# Apply the heatmap processing function
if 'heatmap' in final_df_with_stats.columns:
    heatmap_features = final_df_with_stats['heatmap'].apply(process_heatmap)
    # Flatten the dictionary into columns
    heatmap_df = pd.json_normalize(heatmap_features)
    final_df_with_stats = pd.concat([final_df_with_stats, heatmap_df], axis=1)
    # Drop original heatmap column
    final_df_with_stats.drop(
        columns=['heatmap'], inplace=True, errors='ignore')

# Replace NaN or None values with 0 in the entire dataframe
final_df_with_stats = final_df_with_stats.fillna(0)

# Check the resulting dataframe
print(final_df_with_stats.isnull().sum())
print(final_df_with_stats.head())

# Save the cleaned and processed data to an Excel file
final_df_with_stats.to_csv("cleaned_data.csv", index=False)
