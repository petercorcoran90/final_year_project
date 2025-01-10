import plotly.graph_objects as go
import ast  # For safely parsing string representations of lists
import tkinter as tk
from tkinter.messagebox import showinfo
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd
import io

# Load the cleaned data
data = pd.read_csv("scored_data.csv")


def get_players_by_position(position):
    """Get all players by position with average scores."""
    def position_match(pos_list, target_pos):
        if isinstance(pos_list, str):  # If stored as a string
            try:
                pos_list = ast.literal_eval(pos_list)  # Convert string to list
            except (ValueError, SyntaxError):
                return False
        if isinstance(pos_list, list):  # Check if target position exists in the list
            return target_pos in pos_list
        return False

    # Filter players by position
    position_players = data[data["positions"].apply(
        lambda x: position_match(x, position))]

    # Calculate average score for each player
    position_players.loc[:, "average_score"] = position_players.groupby(
        "name")["predicted_rating"].transform("mean")

    return position_players[["name", "team_name", "market_value", "average_score"]].drop_duplicates()


def plot_player_scores_plotly(player_name):
    """Generate a Plotly graph and display it in the Tkinter GUI."""
    # Filter player data
    player_data = data[data["name"] == player_name]

    # Find the maximum round
    max_round = int(data["round"].max())

    # Merge player data with all valid rounds
    all_rounds = pd.DataFrame({"round": range(1, max_round + 1)})
    player_data = pd.merge(all_rounds, player_data, on="round", how="left")

    # Filter out rows where predicted_rating <= 0
    player_data.loc[player_data["predicted_rating"]
                    <= 0, "predicted_rating"] = None

    # Create the plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=player_data["round"],
        y=player_data["predicted_rating"],
        mode="lines+markers",
        name="Predicted Rating",
        connectgaps=False  # Do not connect gaps in the data
    ))

    # Update layout to show all rounds on the x-axis
    fig.update_layout(
        title=f"Scores for {player_name}",
        xaxis_title="Round",
        yaxis_title="Predicted Rating",
        xaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,  # Force ticks to show every round
            range=[1, max_round]  # Ensure the x-axis starts from round 1
        ),
        yaxis=dict(
            tickmode='linear'
        ),
        template="plotly_white"
    )

    # Convert the Plotly figure to an image
    image_buffer = io.BytesIO()
    fig.write_image(image_buffer, format="png")
    image_buffer.seek(0)

    # Display the image in Tkinter Canvas
    plot_image = Image.open(image_buffer)
    plot_photo = ImageTk.PhotoImage(plot_image)
    canvas.delete("all")  # Clear the previous plot
    canvas.create_image(0, 0, anchor="nw", image=plot_photo)
    canvas.image = plot_photo  # Prevent garbage collection


# Tkinter App
def search_players():
    # Clear the Treeview
    for item in tree.get_children():
        tree.delete(item)

    # Get the input position
    position = position_entry.get()
    if not position:
        showinfo("Error", "Please enter a position.")
        return

    # Get players by position
    players = get_players_by_position(position)

    # Sort players by average_score (descending order)
    players_sorted = players.sort_values(by="average_score", ascending=False)

    # Populate the Treeview with sorted data
    for _, row in players_sorted.iterrows():
        tree.insert("", "end", values=(
            row["name"], row["team_name"], row["market_value"], f"{row['average_score']:.2f}"))


def plot_scores():
    selected_item = tree.focus()
    if not selected_item:
        showinfo("Error", "Please select a player.")
        return
    player_name = tree.item(selected_item)["values"][0]
    plot_player_scores_plotly(player_name)


app = tk.Tk()
app.title("Player Ratings Explorer")

# Set a fixed window size
app.geometry("1000x800")

# Search Frame
search_frame = tk.Frame(app)
search_frame.pack(pady=10)

tk.Label(search_frame, text="Position:").grid(row=0, column=0, padx=5)
position_entry = tk.Entry(search_frame)
position_entry.grid(row=0, column=1, padx=5)
search_button = tk.Button(search_frame, text="Search", command=search_players)
search_button.grid(row=0, column=2, padx=5)

# Results Frame
results_frame = tk.Frame(app)
results_frame.pack(pady=10)

tree = ttk.Treeview(results_frame, columns=(
    "Name", "Team", "Market Value", "Avg Score"), show="headings")
tree.heading("Name", text="Name")
tree.heading("Team", text="Team")
tree.heading("Market Value", text="Market Value")
tree.heading("Avg Score", text="Avg Score")
tree.pack(fill="both", expand=True)

# Graph and Position Info Frame
bottom_frame = tk.Frame(app)
bottom_frame.pack(fill="both", expand=True, pady=10)

# Graph Frame
graph_frame = tk.Frame(bottom_frame)
graph_frame.pack(side="left", fill="both", expand=True)

# Plot Button Frame
plot_button_frame = tk.Frame(graph_frame)
plot_button_frame.pack()

plot_button = tk.Button(
    plot_button_frame, text="Plot Scores", command=plot_scores)
plot_button.pack()

canvas = tk.Canvas(graph_frame, bg="white")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

# Position Information Frame
info_frame = tk.Frame(bottom_frame, width=200)
info_frame.pack(side="right", fill="y", padx=10, pady=10)

positions_info = """
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

info_label = tk.Label(info_frame, text=positions_info, justify="left",
                      anchor="w", font=("Arial", 10))
info_label.pack(fill="both", padx=10, pady=10)

app.mainloop()
