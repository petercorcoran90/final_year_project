import joblib
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_percentage_error, median_absolute_error
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Load the cleaned data
data = pd.read_csv("cleaned_data.csv")

# Separate features and target
features = data.drop(columns=["rating", "_id", "match_id", "name"])
target = data["rating"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42)

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
    steps=[("preprocessor", preprocessor), ("model", LinearRegression())])

# Train the model
model_pipeline.fit(X_train, y_train)

# Evaluate the model
y_pred = model_pipeline.predict(X_test)
print("MAE:", mean_absolute_error(y_test, y_pred))
print("MSE:", mean_squared_error(y_test, y_pred))
print("R2 Score:", r2_score(y_test, y_pred))

# Hyperparameter Tuning with GridSearchCV
param_grid = {
    "model__n_estimators": [50, 100, 200],
    "model__max_depth": [10, 20, None],
    "model__min_samples_split": [2, 5, 10],
}

grid_search = GridSearchCV(
    estimator=Pipeline(
        steps=[("preprocessor", preprocessor),
               ("model", RandomForestRegressor(random_state=42))]
    ),
    param_grid=param_grid,
    cv=5,
    scoring="r2",
    n_jobs=-1,
)

grid_search.fit(X_train, y_train)

# Best parameters and score
print("Best Parameters:", grid_search.best_params_)
print("Best R2 Score (CV):", grid_search.best_score_)

# Train the best model from GridSearchCV
best_model = grid_search.best_estimator_
best_model.fit(X_train, y_train)

# Evaluate the best model
y_pred_best = best_model.predict(X_test)
print("Best Model MAE:", mean_absolute_error(y_test, y_pred_best))
print("Best Model MSE:", mean_squared_error(y_test, y_pred_best))
print("Best Model R2 Score:", r2_score(y_test, y_pred_best))

# Extract feature importance for Random Forest
if isinstance(best_model.named_steps["model"], RandomForestRegressor):
    feature_importance = best_model.named_steps["model"].feature_importances_
    features = numerical_cols.tolist() + list(
        best_model.named_steps["preprocessor"].transformers_[
            1][1].get_feature_names_out(categorical_cols)
    )

    # Create a DataFrame to display importance
    importance_df = pd.DataFrame({
        "Feature": features,
        "Importance": feature_importance
    }).sort_values(by="Importance", ascending=False)

    print("Feature Importances:")
    print(importance_df.head(10))

# Evaluate Model Robustness

# Calculate additional metrics
mape = mean_absolute_percentage_error(y_test, y_pred_best)
median_ae = median_absolute_error(y_test, y_pred_best)

print(f"Mean Absolute Percentage Error (MAPE): {mape:.4f}")
print(f"Median Absolute Error: {median_ae:.4f}")

# Perform k-Fold Cross-Validation
kf = KFold(n_splits=5, shuffle=True, random_state=42)

# Use cross_val_score with the RandomForestRegressor from the pipeline
cv_scores = cross_val_score(
    grid_search.best_estimator_, X_train, y_train, cv=kf, scoring="r2", n_jobs=-1
)

print("k-Fold Cross-Validation R² Scores:", cv_scores)
print("Mean R² Score (k-Fold):", cv_scores.mean())
print("Standard Deviation (k-Fold):", cv_scores.std())

# Save the best model
joblib.dump(best_model, "best_model.pkl")
print("Model saved as 'best_model.pkl'")
