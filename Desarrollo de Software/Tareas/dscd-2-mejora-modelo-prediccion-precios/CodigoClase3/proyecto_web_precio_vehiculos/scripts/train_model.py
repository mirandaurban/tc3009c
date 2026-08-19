import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CATEGORICAL_FEATURES = ["marca", "modelo", "transmision"]
NUMERIC_FEATURES = ["anio", "km"]
FEATURE_ORDER = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "precio"

MODELOS_POR_MARCA = {
    "Nissan": ["Sentra", "Versa"],
    "Mazda": ["CX-5", "Mazda 3"],
    "Volkswagen": ["Jetta", "Vento"],
    "Toyota": ["Corolla", "Yaris"],
    "Chevrolet": ["Aveo", "Onix"],
}

PRECIO_BASE_MARCA = {
    "Nissan": 260000,
    "Mazda": 300000,
    "Volkswagen": 270000,
    "Toyota": 290000,
    "Chevrolet": 230000,
}


def build_synthetic_dataset(seed: int = 42, n_rows: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    marcas = list(PRECIO_BASE_MARCA.keys())

    rows = []
    for _ in range(n_rows):
        marca = rng.choice(marcas)
        modelo = rng.choice(MODELOS_POR_MARCA[marca])
        anio = int(rng.integers(2015, 2024))
        km = int(max(1000, rng.normal((2024 - anio) * 12000, 9000)))
        transmision = rng.choice(["Automatica", "Manual"], p=[0.65, 0.35])

        precio = (
            PRECIO_BASE_MARCA[marca]
            + (anio - 2015) * 18000
            - km * 1.1
            + (5000 if transmision == "Automatica" else 0)
            # ruido amplio: representa factores no capturados (estado real, mantenimiento)
            + rng.normal(0, 30000)
        )
        precio = float(np.clip(precio, 60000, None))

        rows.append(
            {
                "marca": marca,
                "modelo": modelo,
                "anio": anio,
                "km": km,
                "transmision": transmision,
                "precio": round(precio, 2),
            }
        )

    return pd.DataFrame(rows)


def train_and_save() -> None:
    project_root = Path(__file__).resolve().parents[1]
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    df = build_synthetic_dataset(seed=42, n_rows=1500)

    X = df[FEATURE_ORDER]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = mean_squared_error(y_test, pred) ** 0.5
    r2 = r2_score(y_test, pred)

    joblib.dump(model, models_dir / "vehicle_price_v1.joblib")

    metrics = {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "r2": round(float(r2), 4),
        "features": FEATURE_ORDER,
        "target": TARGET,
        "model_type": "LinearRegression",
        "model_version": "v1",
    }
    with open(models_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Modelo y metricas guardados en models/")
    print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | R2: {r2:.4f}")


if __name__ == "__main__":
    train_and_save()
