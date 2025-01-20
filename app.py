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

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]  # Replace with your database name

# Load your dataset
data = pd.read_csv("scored_data.csv")

# Define the UI
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_text("position", "Position:",
                      placeholder="Enter position (e.g., AM, GK)")
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
        # Two columns, each taking 6 units on small screens
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
            classes="display nowrap compact",  # Keep compact style
        )

    @reactive.calc
    def filtered_players():
        """Filter the players based on the position input."""
        df = data.copy()
        df["average_score"] = df.groupby(
            "name")["predicted_rating"].transform("mean")
        df["average_score"] = df["average_score"].round(2)

        position = input.position()
        if position:
            df = df[df["positions"].str.contains(position, na=False)]

        df = df.sort_values(by="average_score", ascending=False)
        # Keep _id for internal logic but exclude it from displayed columns
        df = df[["name", "team_name", "proposedMarketValue",
                 "_id", "average_score"]].drop_duplicates()
        return df.reset_index(drop=True)

    @reactive.effect
    def _():
        """Update the player table widget."""
        df = filtered_players()
        if len(df) > 1000:
            df = df.head(1000)
        # Exclude _id from being displayed in the table
        table_data = df.drop(columns=["_id"]).rename(
            columns={
                "name": "Player Name",
                "team_name": "Team",
                "proposedMarketValue": "Market Value (€)",
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

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=player_data["round"],
            y=player_data["predicted_rating"],
            mode="lines+markers",
            name="Predicted Rating",
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
