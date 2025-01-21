from shiny import App, reactive, render, ui
from itables.widget import ITable
from shinywidgets import output_widget, reactive_read, render_widget
import pandas as pd
import plotly.graph_objects as go
from mplsoccer import Pitch
import seaborn as sns
import matplotlib.pyplot as plt
import tempfile
import os
from pymongo import MongoClient
import json

POSITIONS_INFO = (
    "AM - Attacking Midfielder\n"
    "DC - Central Defender\n"
    "DL - Left Defender\n"
    "DM - Defensive Midfielder\n"
    "DR - Right Defender\n"
    "GK - Goalkeeper\n"
    "LW - Left Wing\n"
    "MC - Central Midfielder\n"
    "ML - Left Midfielder\n"
    "MR - Right Midfielder\n"
    "RW - Right Wing\n"
    "ST - Striker\n"
)


# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]  # Replace with your database name

# Load your dataset
data = pd.read_csv("scored_data.csv")

# Load flag codes from JSON file
with open("flag_codes.json", "r") as file:
    FLAG_CODES = json.load(file)

# Calculate the minimum and maximum market values from the dataset
min_market_value = int(data["proposedMarketValue"].min())
max_market_value = int(data["proposedMarketValue"].max())

# Define CSS for the tooltip
tooltip_css = """
<style>
.tooltip-custom {
    background-color: black;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-size: 14px;
    white-space: pre-wrap;
    text-align: left;
    max-width: 250px;
}
</style>
"""

# Define the UI
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tooltip(
            ui.input_text("position", "Position:",
                          placeholder="Enter position (e.g., AM, GK)"),
            POSITIONS_INFO,
            placement="bottom",  # Tooltip position
            id="position_tooltip",  # Tooltip ID
            class_="tooltip-custom",  # Apply custom CSS class
        ),
        ui.input_slider(
            "budget",
            "Budget (€):",
            min=min_market_value,  # Use minimum market value
            max=max_market_value,  # Use maximum market value
            value=[min_market_value, max_market_value],  # Default range
            step=1000000  # Adjust step size for better slider control
        ),
        ui.card(
            ui.output_ui("player_profile"),
            ui.output_ui("player_profile_info"),  # Player Info
        ),
    ),
    # Layout for Player Table and Heatmap
    ui.layout_columns(
        ui.card(
            ui.card_header("Player Ratings Table"),
            output_widget("player_table"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Player Heatmap"),
            ui.output_image("heatmap_graph"),
            full_screen=True,
        ),
        # Two columns, each taking 7 and 5 units on small screens
        col_widths={"sm": (7, 5)},
    ),
    # Layout for Score Graph
    ui.layout_columns(
        ui.card(
            ui.card_header("Player Score Graph"),
            output_widget("player_score_graph"),
            full_screen=True,
        ),
        # One column taking full width on small screens
        col_widths={"sm": (12)},
    ),
    ui.output_text("selected_row"),
    title="Scouting Tool",
    fillable=True,
)

# Helper function to fetch heatmap data from MongoDB


def get_heatmap_data(player_id):
    """Fetch heatmap data for the specified player ID from all round collections."""
    heatmap_points = []
    player_id = int(player_id)

    for round_num in range(1, 39):  # Assuming 38 rounds in the season
        collection_name = f"round_{round_num}"
        collection = db[collection_name]
        player_data = collection.find_one({"_id": player_id})
        if player_data and "heatmap" in player_data:
            heatmap_points.extend(player_data["heatmap"])

    if not heatmap_points:
        return pd.DataFrame(columns=["x", "y"])

    return pd.DataFrame(heatmap_points)

# Helper function to generate heatmap image


def generate_heatmap_image(player_id):
    """Generate a soccer pitch heatmap image for a player."""
    heatmap_data = get_heatmap_data(player_id)
    if heatmap_data.empty:
        return None

    pitch = Pitch(pitch_type='opta', pitch_color='grass', line_color='white')
    fig, ax = pitch.draw(figsize=(5, 3))

    sns.kdeplot(
        x=heatmap_data["x"],
        y=heatmap_data["y"],
        fill=True,
        thresh=0.015,
        bw_adjust=0.6,
        levels=300,
        cmap='YlOrRd',
        alpha=0.35,
        clip=((0, 100), (0, 100)),
        ax=ax
    )

    ax.axis("off")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    return temp_file.name


def server(input, output, session):
    @render_widget
    def player_table():
        """Create the `ITable` widget for the player table."""
        return ITable(
            caption="Player Ratings Table",
            select=True,
            dom="t",
            scrollY="300px",
            scrollX=True,  # Enable horizontal scrolling
            scrollCollapse=True,
            paging=False,
            classes="display compact",  # Keep compact style
        )

    @reactive.calc
    def filtered_players():
        """Filter the players based on the position input and budget."""
        df = data.copy()

        # Handle missing or invalid values
        # Drop rows with missing key data
        df = df.dropna(subset=["name", "team_name", "proposedMarketValue"])
        # Keep only players with a positive market value
        df = df[df["proposedMarketValue"] > 0]

        # Calculate average score
        df["average_score"] = df.groupby(
            "name")["predicted_rating"].transform("mean")
        df["average_score"] = df["average_score"].round(2)

        # Position filtering
        position = input.position()
        if position:
            df = df[df["positions"].str.contains(position, na=False)]

        # Budget filtering
        budget = input.budget()
        df = df[(df["proposedMarketValue"] >= budget[0]) &
                (df["proposedMarketValue"] <= budget[1])]

        # Sort by average score (descending)
        df = df.sort_values(by="average_score", ascending=False)

        # Format the Market Value column
        df["proposedMarketValue"] = df["proposedMarketValue"].apply(lambda x: f"€{
                                                                    x:,.2f}")

        # Keep only relevant columns
        df = df[["name", "team_name", "proposedMarketValue",
                 "_id", "average_score"]].drop_duplicates()
        return df.reset_index(drop=True)

    @reactive.effect
    def _():
        """Update the player table widget."""
        df = filtered_players()

        # Exclude _id from being displayed in the table
        table_data = df.drop(columns=["_id"]).rename(
            columns={
                "name": "Player Name",
                "team_name": "Team",
                "proposedMarketValue": "Market Value",
                "average_score": "Average Score",
            }
        )
        player_table.widget.update(
            table_data,
            selected_rows=[],  # Reset selected rows
        )

    @render.text
    def selected_row():
        """Display details of the selected row."""
        selected_rows = reactive_read(player_table.widget, "selected_rows")
        df = filtered_players()
        if selected_rows:
            row = df.iloc[selected_rows[0]]
            return f"Selected Player: {row['name']} (Team: {row['team_name']}, Avg Score: {row['average_score']})"
        return "No row selected."

    @render.ui
    def player_profile():
        """Render the player's profile image dynamically."""
        selected_rows = reactive_read(player_table.widget, "selected_rows")
        df = filtered_players()

        # Ensure a row is selected and data is valid
        if selected_rows and not df.empty:
            player_id = df.iloc[selected_rows[0]].get("_id", None)

            # Construct the image URL if player ID is valid
            if player_id:
                image_url = f"https://img.sofascore.com/api/v1/player/{
                    player_id}/image"
                return ui.HTML(f'<img src="{image_url}" alt="Player Image" style="width: 100%; border-radius: 8px;">')

        # Fallback: Provide a placeholder or default message
        return ui.HTML('<div style="text-align: center; font-size: 14px; color: gray;">No Player Selected</div>')

    @render.ui
    def player_profile_info():
        """Render the player's detailed profile information."""
        selected_rows = reactive_read(player_table.widget, "selected_rows")
        df = filtered_players()

        # Ensure a player is selected
        if selected_rows and not df.empty:
            try:
                # Ensure player_id is an integer
                player_id = int(df.iloc[selected_rows[0]].get("_id", None))
                # print(f"Selected player ID: {player_id}")

                # Query the MongoDB players collection
                player_data = db.players.find_one({"_id": player_id})
                # print(f"Player Data for ID {player_id}: {player_data}")

                if player_data:
                    # Extract required fields with fallback values
                    preferred_foot = player_data.get(
                        "preferredFoot", "Unknown")
                    height = f'{player_data.get("height", "Unknown")} cm'
                    jersey_number = player_data.get("jerseyNumber", "Unknown")
                    country = player_data.get(
                        "country", {}).get("name", "Unknown")
                    date_of_birth = pd.to_datetime(
                        player_data.get("dateOfBirthTimestamp", 0), unit="s"
                    ).strftime("%Y-%m-%d")
                    contract_until = pd.to_datetime(
                        player_data.get("contractUntilTimestamp", 0), unit="s"
                    ).strftime("%Y-%m-%d")
                    positions = ", ".join(player_data.get("positions", []))
                    gender = "Male" if player_data.get(
                        "gender") == "M" else "Female"

                    flag_code = next((code for code, name in FLAG_CODES.items(
                    ) if name.lower() == country.lower()), None)

                    # Generate flag HTML
                    flag_html = ""
                    if flag_code:
                        flag_html = f"""
                        <img
                            src="https://flagcdn.com/w20/{flag_code}.png"
                            srcset="https://flagcdn.com/w40/{flag_code}.png 2x"
                            width="20"
                            alt="{country}">
                        """

                    # Create HTML content
                    profile_html = f"""
                    <div style="font-size: 12px; margin-top: 1px;">
                        <p><strong>Preferred Foot:</strong> {preferred_foot}</p>
                        <p><strong>Height:</strong> {height}</p>
                        <p><strong>Jersey Number:</strong> {jersey_number}</p>
                        <p><strong>Country:</strong> {flag_html} {country}</p>
                        <p><strong>Date of Birth:</strong> {date_of_birth}</p>
                        <p><strong>Contract Until:</strong> {contract_until}</p>
                        <p><strong>Positions:</strong> {positions}</p>
                        <p><strong>Gender:</strong> {gender}</p>
                    </div>
                    """
                    return ui.HTML(profile_html)

                # If no data found, print debug message
                # print(f"No player data found for ID {player_id}")

            except Exception as e:
                # Catch and display errors
                print(f"Error in player_profile_info: {e}")

    @render.image
    def heatmap_graph():
        """Render the heatmap graph for the selected player or show an empty pitch on initial load."""
        selected_rows = reactive_read(player_table.widget, "selected_rows")
        df = filtered_players()

        # If no player is selected or the table is empty, display an empty pitch
        if not selected_rows or df.empty:
            pitch = Pitch(pitch_type='opta', pitch_color='grass',
                          line_color='white')
            fig, ax = pitch.draw(figsize=(5, 3))
            ax.axis("off")

            # Save the empty pitch to a temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".png")
            plt.savefig(temp_file.name, format="png",
                        bbox_inches="tight", dpi=100)
            plt.close(fig)
            return {"src": temp_file.name, "alt": "Empty Pitch", "delete": True}

        # Fetch the player's ID
        player_id = df.iloc[selected_rows[0]].get("_id", None)

        # Ensure we have a valid player ID
        if player_id is None:
            return {"src": None, "alt": "No Player ID Found"}

        # Attempt to generate the heatmap image
        heatmap_path = generate_heatmap_image(player_id)
        if heatmap_path and os.path.exists(heatmap_path):
            return {"src": heatmap_path, "alt": "Player Heatmap", "delete": True}
        else:
            return {"src": None, "alt": "No Heatmap Data Available"}

    # Create hover information with more details
    def format_hover_info(row):
        """Format the hover information for each point with nicer labels."""
        details = [
            # Always include the round info
            f"<b>Round:</b> {int(row['round'])}"]

        # Mapping of column names to display labels
        column_labels = {
            "accuratePass": "Accurate Passes",
            "aerialLost": "Aerial Lost",
            "challengeLost": "Challenges Lost",
            "duelLost": "Duels Lost",
            "duelWon": "Duels Won",
            "fouls": "Fouls",
            "goalAssist": "<b>Assists</b>",
            "minutesPlayed": "Minutes Played",
            "possessionLostCtrl": "Possession Lost",
            "totalPass": "Total Passes",
            "totalTackle": "Tackles",
            "touches": "Touches",
            "accurateCross": "Accurate Crosses",
            "aerialWon": "Aerial Won",
            "bigChanceCreated": "<b>Big Chances Created</b>",
            "blockedScoringAttempt": "Blocked Shots",
            "expectedAssists": "<b>xA</b>",
            "expectedGoals": "<b>xG</b>",
            "keyPass": "Key Passes",
            "totalContest": "Contests",
            "totalCross": "Crosses",
            "wasFouled": "Was Fouled",
            "wonContest": "Contests Won",
            "accurateLongBalls": "Accurate Long Balls",
            "dispossessed": "Dispossessed",
            "onTargetScoringAttempt": "On-Target Shots",
            "totalLongBalls": "Long Balls",
            "interceptionWon": "Interceptions",
            "shotOffTarget": "Shots Off-Target",
            "totalClearance": "Clearances",
            "errorLeadToAShot": "Errors Leading to Shots",
            "outfielderBlock": "Outfielder Blocks",
            "goalsPrevented": "Goals Prevented",
            "goodHighClaim": "High Claims",
            "savedShotsFromInsideTheBox": "Saves Inside Box",
            "saves": "Saves",
            "bigChanceMissed": "<b>Big Chances Missed</b>",
            "goals": "<b>Goals</b>",
            "totalOffside": "Offsides",
            "accurateKeeperSweeper": "Accurate Keeper Sweeper",
            "punches": "Punches",
            "totalKeeperSweeper": "Total Keeper Sweeper",
            "clearanceOffLine": "Clearances Off Line",
            "hitWoodwork": "Hit Woodwork",
            "ownGoals": "Own Goals",
            "penaltyWon": "Penalties Won",
            "penaltyConceded": "Penalties Conceded",
            "lastManTackle": "Last-Man Tackles",
            "errorLeadToAGoal": "Errors Leading to Goals",
            "penaltyMiss": "Penalties Missed",
            "penaltySave": "Penalties Saved",
            "card_info": "Card Info",
        }

        # Dynamically add column info if the value is numeric and greater than 0
        for col, label in column_labels.items():
            if col in row and pd.notna(row[col]):
                try:
                    value = float(row[col])  # Attempt to convert to float
                    if value > 0:
                        details.append(f"{label}: {value}")
                except ValueError:
                    # Skip non-numeric values
                    pass

        # Add predicted rating if present
        if pd.notna(row["predicted_rating"]):
            details.append(
                f"<b>Predicted Rating:</b> {row['predicted_rating']:.2f}")

        return "<br>".join(details)

    @render_widget
    def player_score_graph():
        """Render the player score graph for the selected row."""
        selected_rows = reactive_read(player_table.widget, "selected_rows")
        df = filtered_players()
        if not selected_rows:
            return go.Figure().update_layout(title="No Player Selected", template="plotly_white")

        player_name = df.iloc[selected_rows[0]]["name"]
        player_data = data[data["name"] == player_name]
        max_round = int(data["round"].max())
        all_rounds = pd.DataFrame({"round": range(1, max_round + 1)})
        player_data = pd.merge(all_rounds, player_data, on="round", how="left")
        player_data.loc[player_data["predicted_rating"]
                        <= 0, "predicted_rating"] = None

        # Format hover info for each point
        player_data["hover_info"] = player_data.apply(
            format_hover_info, axis=1)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=player_data["round"],
            y=player_data["predicted_rating"],
            mode="lines+markers",
            name="",
            hovertemplate="%{text}",  # Use the hover template
            text=player_data["hover_info"],  # Assign hover info to text
            textposition="middle center",
            connectgaps=False,
        ))
        fig.update_layout(
            title=f"Scores for {player_name}",
            xaxis_title="Round",
            yaxis_title="Predicted Rating",
            xaxis=dict(tickmode="linear"),
            yaxis=dict(tickmode="linear"),
            template="plotly_white",
        )
        return fig


app = App(app_ui, server)
