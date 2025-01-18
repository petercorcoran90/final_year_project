import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from mplsoccer import Pitch
import seaborn as sns

# MongoDB connection setup
# Replace with your MongoDB URI
client = MongoClient("mongodb://localhost:27017/")
db = client["soccer_db"]  # Replace with your database name


def get_heatmap_data(player_id):
    """
    Fetch heatmap data for the specified player ID from all round collections.
    """
    heatmap_points = []

    # Traverse through all round collections
    for round_num in range(1, 39):  # Assuming 38 rounds in the season
        collection_name = f"round_{round_num}"
        collection = db[collection_name]
        player_data = collection.find_one({"_id": player_id})
        if player_data and "heatmap" in player_data:
            heatmap_points.extend(player_data["heatmap"])

    if not heatmap_points:
        print(f"No heatmap data found for player ID {player_id}.")
        return pd.DataFrame(columns=["x", "y"])

    return pd.DataFrame(heatmap_points)


def main():
    # Ask for player ID
    player_id = 982780

    # Fetch heatmap data
    heatmap_data = get_heatmap_data(player_id)

    if heatmap_data.empty:
        print(f"No heatmap data available for player ID {player_id}.")
        return

    # Create the pitch
    pitch = Pitch(pitch_type='opta', pitch_color='grass',
                  line_color='white', stripe=True)
    fig, ax = pitch.draw(figsize=(10, 7))

    # Plot the KDE heatmap
    sns.kdeplot(
        x=heatmap_data['x'],
        y=heatmap_data['y'],
        fill=True,
        thresh=0.015,      # Suppress very low-density areas
        bw_adjust=0.6,   # Sensitivity to clustering
        levels=300,  # Number of contour levels
        cmap='YlOrRd',   # Colormap for the heatmap
        alpha=0.35,       # Adjust transparency
        clip=((0, 100), (0, 100)),  # Clip KDE within the pitch boundaries
        ax=ax
    )

    # Remove the axis for a cleaner look
    ax.axis('off')

    # Show the plot
    plt.show()


if __name__ == "__main__":
    main()
