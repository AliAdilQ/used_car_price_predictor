"""Load the bundled pipeline once per app process; never train during requests."""
import json
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning

from services.catalog import FEATURES


class ModelUnavailable(RuntimeError):
    pass


class PredictionService:
    def __init__(self, model_path, metrics_path):
        if not model_path.exists() or not metrics_path.exists():
            raise ModelUnavailable("Model files missing. Run python train_model.py.")
        try:
            self.metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                self.pipeline = joblib.load(model_path)
        except (OSError, ValueError, InconsistentVersionWarning) as error:
            raise ModelUnavailable("Install pinned requirements and run python train_model.py.") from error

    def predict(self, inputs):
        row = pd.DataFrame([{key: inputs[key] for key in FEATURES}])
        price = float(self.pipeline.predict(row)[0])
        if not np.isfinite(price) or price <= 0:
            raise ModelUnavailable("The model returned an invalid estimate.")
        price = round(price, 2)
        band = self.metrics["residual_band_usd"]
        return dict(predicted_price=price, price_lower=round(max(0, price - band), 2),
                    price_upper=round(price + band, 2),
                    model_name=self.metrics["selected_model"])
