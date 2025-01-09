from pymongo import MongoClient
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib  # For saving and loading the model

# Step 1: MongoDB Connection and Data Retrieval
client = MongoClient("mongodb://localhost:27017/")
db = client['soccer_db']

# Assuming each game round is stored in a different collection like 'round_1', 'round_2', etc.
rounds = ['round_1', 'round_2', 'round_3']  # Add more rounds as necessary

# Retrieve all game stats for the player
player_id = 982780
data = []
for round_name in rounds:
    collection = db[round_name]
    result = collection.find_one({"_id": player_id})
    if result:
        result['round'] = round_name  # Add round information for reference
        data.append(result)

# Convert to DataFrame
df = pd.DataFrame(data)

# Example player position data from the SofaScore API
player_position_data = {
    "player_id": 982780,
    "positions": ["RW", "AM"]  # From SofaScore API
}

# Add player positions to the DataFrame
df['positions'] = [player_position_data['positions']] * len(df)

# Step 2: Data Preprocessing and Cleaning
# Handle missing data (fill missing values with 0)
df.fillna(0, inplace=True)

# Step 3: Feature Engineering (Position-Specific Features)
if "RW" in df['positions'].iloc[0] or "LW" in df['positions'].iloc[0]:
    # Features important for Winger (RW, LW)
    df['cross_accuracy'] = df['accurateCross'] / \
        df['totalCross'].replace(0, 1)  # Avoid division by zero
    df['assist_rate'] = df['goalAssist'] / \
        df['keyPass'].replace(0, 1)  # Avoid division by zero
    df['dribble_success_rate'] = df['duelWon'] / \
        (df['duelWon'] + df['duelLost']).replace(0, 1)  # Avoid division by zero
    # Use touches as an estimate for involvement in attack
    df['touch_in_final_third'] = df['touches']

if "AM" in df['positions'].iloc[0]:
    # Features important for Attacking Midfielder (AM)
    df['goal_contribution'] = df['expectedGoals'] + df['expectedAssists']
    df['key_pass_rate'] = df['keyPass'] / \
        df['totalPass'].replace(0, 1)  # Avoid division by zero
    # Approximation: use accurate passes as progressive passes
    df['progressive_passes'] = df['accuratePass']

# Fill any newly created NaNs (e.g., division by zero)
df.fillna(0, inplace=True)

# Step 4: Label Creation (Performance Trend)
# For now, let's use a simple measure: difference in goal contribution between rounds
df['goal_contribution_diff'] = df['goal_contribution'].diff().fillna(0)
df['performance_trend'] = df['goal_contribution_diff'].apply(
    lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

# Step 5: Prepare Features and Labels for Modeling
# Select the important features for the specific position
features = ['expectedGoals', 'expectedAssists', 'cross_accuracy',
            'goal_contribution', 'dribble_success_rate', 'touch_in_final_third']
X = df[features]
y = df['performance_trend']

# Train-test split (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

# Step 6: Train the Model (Random Forest)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Step 7: Make Predictions and Evaluate the Model
y_pred = model.predict(X_test)

# Model accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f'Model Accuracy: {accuracy * 100:.2f}%')

# Step 8: Save the Model for Future Use
joblib.dump(model, 'player_performance_model.pkl')
print("Model saved as 'player_performance_model.pkl'.")

# Step 9: Load the Model for Future Use
loaded_model = joblib.load('player_performance_model.pkl')
print("Model loaded from 'player_performance_model.pkl'.")

# Step 10: Display Data with Features and Predictions
print(df[['round', 'expectedGoals', 'goal_contribution', 'performance_trend']].head())
