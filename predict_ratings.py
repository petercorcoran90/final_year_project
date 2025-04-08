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

# Load the cleaned dataset from a CSV file into a pandas DataFrame.
data = pd.read_csv("cleaned_data.csv")

# Separate the dataset into features (input variables) and target (output variable).
# Here, 'rating' is the target variable and we remove other columns that are not used as features.
features = data.drop(columns=["rating", "_id", "match_id", "name"])
target = data["rating"]

# Split the data into training and testing sets.
# 80% is used for training and 20% for testing. Setting random_state ensures reproducibility.
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42)

# Identify which columns are numerical and which are categorical based on data types.
numerical_cols = X_train.select_dtypes(include=["float64", "int64"]).columns
categorical_cols = X_train.select_dtypes(include=["object"]).columns

# Create a pipeline to preprocess numerical features by scaling them.
numerical_pipeline = Pipeline(steps=[("scaler", StandardScaler())])

# Create a pipeline to preprocess categorical features by one-hot encoding them.
# The encoder will ignore categories not seen during training.
categorical_pipeline = Pipeline(
    steps=[("encoder", OneHotEncoder(handle_unknown="ignore"))])

# Combine the numerical and categorical pipelines into one preprocessor.
# This applies the correct preprocessing to each type of column.
preprocessor = ColumnTransformer(
    transformers=[
        ("num", numerical_pipeline, numerical_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ]
)

# Build a machine learning pipeline that first preprocesses the data,
# then applies a Linear Regression model.
model_pipeline = Pipeline(
    steps=[("preprocessor", preprocessor), ("model", LinearRegression())])

# Train the Linear Regression model using the training data.
model_pipeline.fit(X_train, y_train)

# Predict the target variable for the test set.
y_pred = model_pipeline.predict(X_test)

# Calculate and print evaluation metrics: Mean Absolute Error, Mean Squared Error, and R² Score.
print("MAE:", mean_absolute_error(y_test, y_pred))
print("MSE:", mean_squared_error(y_test, y_pred))
print("R2 Score:", r2_score(y_test, y_pred))

# Define a grid of hyperparameters to tune for a RandomForestRegressor model.
param_grid = {
    # Number of trees in the forest.
    "model__n_estimators": [50, 100, 200],
    # Maximum depth of the trees.
    "model__max_depth": [10, 20, None],
    # Minimum samples required to split a node.
    "model__min_samples_split": [2, 5, 10],
}

# Create a GridSearchCV object to search for the best hyperparameters using cross-validation.
# A new pipeline is built here using the preprocessor and a RandomForestRegressor.
grid_search = GridSearchCV(
    estimator=Pipeline(
        steps=[("preprocessor", preprocessor),
               ("model", RandomForestRegressor(random_state=42))]
    ),
    param_grid=param_grid,
    cv=5,               # Use 5-fold cross-validation.
    scoring="r2",       # Evaluate based on the R² score.
    n_jobs=-1,          # Use all available CPU cores.
)

# Run the grid search on the training data to find the best hyperparameters.
grid_search.fit(X_train, y_train)

# Print the best hyperparameters and the corresponding cross-validated R² score.
print("Best Parameters:", grid_search.best_params_)
print("Best R2 Score (CV):", grid_search.best_score_)

# Extract the best model found by grid search and retrain it on the entire training set.
best_model = grid_search.best_estimator_
best_model.fit(X_train, y_train)

# Evaluate the best model by predicting on the test set and calculating evaluation metrics.
y_pred_best = best_model.predict(X_test)
print("Best Model MAE:", mean_absolute_error(y_test, y_pred_best))
print("Best Model MSE:", mean_squared_error(y_test, y_pred_best))
print("Best Model R2 Score:", r2_score(y_test, y_pred_best))

# If the best model is a RandomForestRegressor, extract and display the feature importances.
if isinstance(best_model.named_steps["model"], RandomForestRegressor):
    # Get the feature importances from the Random Forest model.
    feature_importance = best_model.named_steps["model"].feature_importances_
    # Combine numerical feature names with one-hot encoded categorical feature names.
    features = numerical_cols.tolist() + list(
        best_model.named_steps["preprocessor"].transformers_[
            1][1].get_feature_names_out(categorical_cols)
    )

    # Create a DataFrame that shows each feature and its corresponding importance,
    # then sort it in descending order to show the most important features first.
    importance_df = pd.DataFrame({
        "Feature": features,
        "Importance": feature_importance
    }).sort_values(by="Importance", ascending=False)

    print("Feature Importances:")
    # Display the top 10 most important features.
    print(importance_df.head(10))

# Calculate additional metrics to evaluate the model's robustness.
# Mean Absolute Percentage Error (MAPE) shows the error in percentage.
# Median Absolute Error gives the median of the absolute errors.
mape = mean_absolute_percentage_error(y_test, y_pred_best)
median_ae = median_absolute_error(y_test, y_pred_best)

print(f"Mean Absolute Percentage Error (MAPE): {mape:.4f}")
print(f"Median Absolute Error: {median_ae:.4f}")

# Perform 5-fold cross-validation to further evaluate the model's performance.
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(
    grid_search.best_estimator_, X_train, y_train, cv=kf, scoring="r2", n_jobs=-1
)

# Print the R² scores for each fold, as well as the mean and standard deviation.
print("k-Fold Cross-Validation R² Scores:", cv_scores)
print("Mean R² Score (k-Fold):", cv_scores.mean())
print("Standard Deviation (k-Fold):", cv_scores.std())

# Save the best model to a file so that it can be loaded later without retraining.
joblib.dump(best_model, "best_model.pkl")
print("Model saved as 'best_model.pkl'")
