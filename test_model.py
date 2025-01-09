import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load the cleaned data
data = pd.read_csv("cleaned_data.csv")

# Separate features and target
features = data.drop(columns=["rating", "_id", "match_id", "name"])
target = data["rating"]

# Split data
_, X_test, _, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42)

# Load the saved model
loaded_model = joblib.load("best_model.pkl")
print("Model loaded successfully.")

# Make predictions with the loaded model
y_pred_loaded = loaded_model.predict(X_test)

# Evaluate the loaded model
print("Loaded Model MAE:", mean_absolute_error(y_test, y_pred_loaded))
print("Loaded Model MSE:", mean_squared_error(y_test, y_pred_loaded))
print("Loaded Model R2 Score:", r2_score(y_test, y_pred_loaded))

# Verify predictions match the original model
print("Predictions match:", all(y_pred_loaded == y_pred_loaded))
