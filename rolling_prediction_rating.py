import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load the cleaned data
data = pd.read_csv("cleaned_data.csv")

# Sort by round to ensure correct chronological order
data = data.sort_values(by=["round"])

# Step 1: Split Data
train_rounds = [1, 2, 3, 4, 5]   # Train on first 5 rounds
predict_rounds = list(range(6, 16))  # Predict rounds 6-15
test_rounds = predict_rounds  # Use the same rounds for evaluation

train_data = data[data["round"].isin(train_rounds)]
test_data = data[data["round"].isin(test_rounds)]

# Drop unnecessary columns
features = data.drop(columns=["rating", "_id", "match_id", "name"])
feature_columns = features.columns

# Separate features and target
X_train = train_data[feature_columns]
y_train = train_data["rating"]

X_test = test_data[feature_columns]
y_test = test_data["rating"]

# Preprocessing pipelines
numerical_cols = X_train.select_dtypes(include=["float64", "int64"]).columns
categorical_cols = X_train.select_dtypes(include=["object"]).columns

numerical_pipeline = Pipeline(steps=[("scaler", StandardScaler())])
categorical_pipeline = Pipeline(
    steps=[("encoder", OneHotEncoder(handle_unknown="ignore"))])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numerical_pipeline, numerical_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ]
)

# Model pipeline
model_pipeline = Pipeline(
    steps=[("preprocessor", preprocessor), ("model",
                                            RandomForestRegressor(n_estimators=100, random_state=42))]
)

# Step 2: Train the Model
print("Training the model on rounds 1-5...")
model_pipeline.fit(X_train, y_train)

# Step 3: Predict Ratings for Rounds 6-15
print("Predicting player ratings for rounds 6-15...")
y_pred = model_pipeline.predict(X_test)

# Step 4: Evaluate Predictions
print("\nModel Performance on Rounds 6-15:")
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MAE: {mae:.4f}")
print(f"MSE: {mse:.4f}")
print(f"R2 Score: {r2:.4f}")

# Step 5: Compare Predictions vs Actual
comparison_df = test_data[["_id", "name", "round", "rating"]].copy()
comparison_df["predicted_rating"] = y_pred

# Save predictions to CSV
comparison_df.to_csv("predicted_vs_actual.csv", index=False)
print("\nSaved predictions to 'predicted_vs_actual.csv'.")
