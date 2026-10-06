"""Select on validation data, then evaluate the winner on an untouched test set."""
import hashlib
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import BASE_DIR
from services.catalog import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES


def evaluate(actual, predicted):
    return {"mae": round(float(mean_absolute_error(actual, predicted)), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(actual, predicted))), 2),
            "r2": round(float(r2_score(actual, predicted)), 6)}


def train():
    dataset_path = BASE_DIR / "data" / "used_cars.csv"
    if not dataset_path.exists():
        from generate_dataset import generate_dataset
        generate_dataset()
    raw = pd.read_csv(dataset_path)
    frame = raw.drop_duplicates().copy()
    for column in NUMERIC_FEATURES + ["price"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=["price", "year"])
    frame = frame[frame.price > 0].copy()
    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].str.strip().replace("", np.nan)
    reference_year = int((frame.year + frame.car_age).dropna().mode().iloc[0])
    frame["car_age"] = reference_year - frame.year
    x = frame[FEATURES]
    y = frame.price
    x_dev, x_test, y_dev, y_test = train_test_split(x, y, test_size=.2, random_state=42)
    x_train, x_val, y_train, y_val = train_test_split(
        x_dev, y_dev, test_size=.25, random_state=42)
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                            ("encode", OneHotEncoder(handle_unknown="ignore",
                                                     sparse_output=False))])
    preprocessor = ColumnTransformer([("numeric", numeric, NUMERIC_FEATURES),
                                      ("category", categorical, CATEGORICAL_FEATURES)])
    regressors = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=2,
                                               random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=280, max_depth=3, learning_rate=.06, loss="huber", random_state=42),
    }
    comparisons, pipelines = [], {}
    for name, regressor in regressors.items():
        # Log prices improve proportional error and ensure positive predictions.
        pipeline = Pipeline([
            ("preprocess", clone(preprocessor)),
            ("regressor", TransformedTargetRegressor(
                regressor=regressor, func=np.log1p, inverse_func=np.expm1)),
        ])
        pipeline.fit(x_train, y_train)
        score = evaluate(y_val, pipeline.predict(x_val))
        comparisons.append({"name": name, **score})
        pipelines[name] = pipeline
        print(f"{name:20s} R²={score['r2']:.4f}  RMSE=${score['rmse']:,.2f}  MAE=${score['mae']:,.2f}")
    winner = max(comparisons, key=lambda score: (score["r2"], -score["rmse"]))
    best = pipelines[winner["name"]]
    best.fit(x_dev, y_dev)
    predicted = best.predict(x_test)
    test_metrics = evaluate(y_test, predicted)
    band = round(float(np.quantile(np.abs(y_test - predicted), .9)), 2)
    metadata = {
        "selected_model": winner["name"], "currency": "USD",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "reference_year": reference_year, "sklearn_version": sklearn.__version__,
        "dataset_type": "synthetic", "dataset_rows": len(frame),
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "dropped_rows": len(raw) - len(frame), "features": FEATURES,
        "split": {"training": len(x_train), "validation": len(x_val),
                  "test": len(x_test), "final_fit": len(x_dev)},
        "selection": "Highest validation R², then lowest validation RMSE",
        "validation_models": comparisons, "test_metrics": test_metrics,
        "residual_band_usd": band,
        "band_description": "90th percentile absolute test residual; illustrative, not a calibrated confidence interval",
        "training_bounds": {col: {"min": float(x_dev[col].min()),
                                  "max": float(x_dev[col].max())}
                            for col in NUMERIC_FEATURES},
    }
    output = BASE_DIR / "models"
    output.mkdir(exist_ok=True)
    joblib.dump(best, output / "car_price_model.pkl", compress=3)
    (output / "model_metrics.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {winner['name']}; untouched test: {test_metrics}")
    return metadata


if __name__ == "__main__":
    train()
