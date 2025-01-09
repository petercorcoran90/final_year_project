import pandas as pd
import joblib

# Load the trained model
model = joblib.load("best_model.pkl")
print("Model loaded successfully.")

# Load the cleaned data
data = pd.read_csv("cleaned_data.csv")

# Create a copy of the data and drop the 'rating' column
data_to_score = data.copy()
if "rating" in data_to_score.columns:
    data_to_score.drop(columns=["rating"], inplace=True)

# Ensure the feature columns match the training set
features_to_score = data_to_score.drop(columns=["_id", "match_id", "name"])

# Predict ratings
predicted_ratings = model.predict(features_to_score)

# Add predictions to the dataset
data_to_score["predicted_rating"] = predicted_ratings

# Save the updated dataset
data_to_score.to_csv("scored_data.csv", index=False)
print("Scored data saved as 'scored_data.csv'.")
