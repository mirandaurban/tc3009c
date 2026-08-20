from pathlib import Path

import joblib
import pandas as pd

MODEL_VERSION = "v1_extratrees"

CATEGORICAL_FEATURES = ["name", "fuel", "seats", "seller_type", "transmission", "owner"]
NUMERIC_FEATURES = ["year", "km_driven", "mileage", "engine", "max_power", "torque"]
FEATURE_ORDER = CATEGORICAL_FEATURES + NUMERIC_FEATURES

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "vehicle_price_exp3.joblib"
_model = None


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. Run scripts/train_model.py first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def predict(payload: dict) -> dict:
    model = get_model()
    row = {k: payload[k] for k in FEATURE_ORDER}
    sample = pd.DataFrame([row], columns=FEATURE_ORDER)

    estimated_price = float(model.predict(sample)[0])

    return {
        "estimated_price": round(estimated_price, 2),
        "currency": "MXN",
        "model_version": MODEL_VERSION,
    }