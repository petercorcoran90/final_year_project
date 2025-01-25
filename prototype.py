import plotly.graph_objects as go
import ast
import tkinter as tk
from tkinter.messagebox import showinfo
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd
import io
from pymongo import MongoClient
from mplsoccer import Pitch
import seaborn as sns
import matplotlib.pyplot as plt

# Load the cleaned data
data = pd.read_csv("scored_data.csv")

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]  # Replace with your database name

POSITIONS_INFO = """
AM - Attacking Midfielder
DC - Central Defender
DL - Left Defender
DM - Defensive Midfielder
DR - Right Defender
GK - Goalkeeper
LW - Left Wing
MC - Central Midfielder
ML - Left Midfielder
MR - Right Midfielder
RW - Right Wing
ST - Striker
"""


def get_players_by_position(position):
    """Get all players by position with average scores."""
    def position_match(pos_list, target_pos):
        if isinstance(pos_list, str):
            try:
                pos_list = ast.literal_eval(pos_list)
            except (ValueError, SyntaxError):
                return False
        if isinstance(pos_list, list):
            return target_pos in pos_list
        return False

    # Filter players by position and create a copy
    position_players = data[data["positions"].apply(
        lambda x: position_match(x, position))].copy()

    # Calculate average score for each player
    position_players["average_score"] = position_players.groupby(
        "name")["predicted_rating"].transform("mean")

    return position_players[["name", "team_name", "proposedMarketValue", "average_score"]].drop_duplicates()


def get_heatmap_data(player_id):
    """Fetch heatmap data for the specified player ID from all round collections."""
    heatmap_points = []

    # Ensure player_id is treated as an integer
    player_id = int(player_id)

    # Traverse through all round collections
    for round_num in range(1, 39):  # Assuming 38 rounds in the season
        collection_name = f"round_{round_num}"
        collection = db[collection_name]
        player_data = collection.find_one(
            {"_id": player_id})  # Ensure _id is an integer
        if player_data and "heatmap" in player_data:
            heatmap_points.extend(player_data["heatmap"])

    # Return the heatmap points as a DataFrame
    if not heatmap_points:
        return pd.DataFrame(columns=["x", "y"])

    return pd.DataFrame(heatmap_points)


def generate_heatmap_image(player_id):
    # print(f"Generating heatmap for Player ID: {player_id}")
    """Generate heatmap image for a player."""
    heatmap_data = get_heatmap_data(player_id)
    if heatmap_data.empty:
        return None

    print(f"Heatmap data points for Player ID {
          player_id}: {len(heatmap_data)}")
    pitch = Pitch(pitch_type='opta', pitch_color='grass',
                  line_color='white', stripe=True)
    fig, ax = pitch.draw(figsize=(5, 3))

    sns.kdeplot(
        x=heatmap_data['x'],
        y=heatmap_data['y'],
        fill=True,
        thresh=0.015,
        bw_adjust=0.6,
        levels=300,
        cmap='YlOrRd',
        alpha=0.35,
        clip=((0, 100), (0, 100)),
        ax=ax
    )

    ax.axis('off')
    image_buffer = io.BytesIO()
    fig.savefig(image_buffer, format="png", bbox_inches='tight', dpi=100)
    plt.close(fig)
    image_buffer.seek(0)

    return Image.open(image_buffer)


def plot_player_scores_plotly(player_name, player_id):
    """Generate and display player score graph and heatmap."""
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
        connectgaps=False
    ))
    fig.update_layout(
        title=f"Scores for {player_name}",
        xaxis_title="Round",
        yaxis_title="Predicted Rating",
        xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[1, max_round]),
        yaxis=dict(tickmode='linear'),
        template="plotly_white"
    )

    # Save and display the score graph
    image_buffer = io.BytesIO()
    fig.write_image(image_buffer, format="png")
    image_buffer.seek(0)
    plot_image = Image.open(image_buffer)
    plot_photo = ImageTk.PhotoImage(plot_image)
    canvas.delete("all")
    canvas.create_image(0, 0, anchor="nw", image=plot_photo)
    canvas.image = plot_photo

    # Plot Heatmap
    heatmap_image = generate_heatmap_image(player_id)
    heatmap_canvas.delete("all")  # Clear the canvas
    if heatmap_image:
        heatmap_photo = ImageTk.PhotoImage(heatmap_image)
        heatmap_canvas.create_image(0, 0, anchor="nw", image=heatmap_photo)
        heatmap_canvas.image = heatmap_photo
    else:
        heatmap_canvas.create_text(100, 100, text="No Heatmap Data",
                                   anchor="center", font=("Arial", 14))

    # Always display Positions Info Below the Heatmap
    heatmap_canvas.create_text(
        100, 300, text=POSITIONS_INFO, anchor="nw",
        font=("Arial", 10), justify="left", fill="black"
    )


def search_players():
    for item in tree.get_children():
        tree.delete(item)

    position = position_entry.get()
    if not position:
        showinfo("Error", "Please enter a position.")
        return

    players = get_players_by_position(position)
    update_treeview(players.sort_values(by="average_score", ascending=False))


def update_treeview(players):
    for _, row in players.iterrows():
        tree.insert("", "end", values=(
            row["name"], row["team_name"], f"${row['proposedMarketValue']:,}",
            f"{row['average_score']:.2f}"))


def on_row_click(event):
    # print("on_row_click triggered")
    selected_item = tree.focus()
    if not selected_item:
        showinfo("Error", "Please select a player.")
        return

    # Get the player's name from the selected row in the Treeview
    player_name = tree.item(selected_item)["values"][0]
    # print(f"Selected Player Name: {player_name}")

    # Open the CSV file and look for the player's _id based on their name
    scored_data = pd.read_csv("scored_data.csv")
    player_info = scored_data[scored_data["name"] == player_name]
    if player_info.empty:
        showinfo("Error", f"No data found for player '{
                 player_name}' in the CSV.")
        return

    # Retrieve the player's _id (unique identifier)
    player_id = player_info.iloc[0]["_id"]
    # print(f"Player ID: {player_id}")

    # Update the plot and heatmap for the selected player
    plot_player_scores_plotly(player_name, player_id)


def initialize_heatmap_canvas():
    """Display default text (positions info) on the heatmap canvas."""
    heatmap_canvas.delete("all")  # Clear the canvas
    heatmap_canvas.create_text(
        100, 300, text=POSITIONS_INFO, anchor="nw",
        font=("Arial", 10), justify="left", fill="black"
    )


app = tk.Tk()
app.title("Player Ratings Explorer")
app.geometry("1200x850")

search_frame = tk.Frame(app)
search_frame.pack(pady=10)


tk.Label(search_frame, text="Position:").grid(row=0, column=0, padx=5)
position_entry = tk.Entry(search_frame)
position_entry.grid(row=0, column=1, padx=5)
search_button = tk.Button(search_frame, text="Search", command=search_players)
search_button.grid(row=0, column=2, padx=5)

results_frame = tk.Frame(app)
results_frame.pack(pady=10)

columns = ("Name", "Team", "Market Value", "Avg Score")
tree = ttk.Treeview(results_frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(fill="both", expand=True)

# Search Frame
search_frame = tk.Frame(app)
search_frame.pack(pady=10)

tree.bind("<ButtonRelease-1>", on_row_click)

bottom_frame = tk.Frame(app)
bottom_frame.pack(fill="both", expand=True, pady=10)

graph_frame = tk.Frame(bottom_frame)
graph_frame.pack(side="left", fill="both", expand=True)

canvas = tk.Canvas(graph_frame, bg="white", width=500, height=500)
canvas.pack(fill="both", expand=True, padx=10, pady=10)

heatmap_frame = tk.Frame(bottom_frame)
heatmap_frame.pack(side="right", fill="both", expand=True)

heatmap_canvas = tk.Canvas(heatmap_frame, bg="white", width=200, height=100)
heatmap_canvas.pack(fill="both", expand=True, padx=10, pady=10)

# Initialize the canvas with positions info
initialize_heatmap_canvas()

app.mainloop()
