from pathlib import Path

import joblib
import pandas as pd

MODEL_VERSION = "v1"
FEATURE_ORDER = ["marca", "modelo", "anio", "km", "transmision"]

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "vehicle_price_v1.joblib"
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
