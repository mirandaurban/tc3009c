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
from sklearn.impute import SimpleImputer # Para experimento 1


# Dirección del dataset
DIRECTORY = Path(__file__).resolve().parent.parent
DATA_PATH = DIRECTORY / "data" / "Car details v3.csv"

# Variables predictorias y objetivo que usará el sistema
CATEGORICAL_FEATURES = ["name", "fuel", "seats", "seller_type", "transmission", "owner"]
NUMERIC_FEATURES = ["year", "km_driven", "mileage", "engine", "max_power", "torque"]
FEATURE_ORDER = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "selling_price"

def clean_numeric_units(series: pd.Series) -> pd.Series:
    """
    Extrae el primer número de columnas '74 bhp', etc.
    """
    return pd.to_numeric(
        series.astype(str).str.extract(r"([\d.]+)")[0], errors="coerce"
    )

 def load_data(path: Path) -> pd.DataFrame:
    """
    Baseline data load
    """
    df = pd.read_csv(path, sep=",")
    df.columns = [c.strip() for c in df.columns]

    for col in ["mileage", "engine", "max_power", "torque"]:
        df[col] = clean_numeric_units(df[col])

    df["seats"] = df["seats"].astype(str)

    n_before = len(df)
    df = df.dropna(subset=NUMERIC_FEATURES + [TARGET])
    n_after = len(df)
    print(f"Filas eliminadas por NaN: {n_before - n_after} de {n_before} ({(n_before-n_after)/n_before:.1%})")

    return df

def train_and_save() -> None:
    df = load_data(DATA_PATH) # Cargar datos primero

    project_root = Path(__file__).resolve().parents[1]
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)


    X = df[FEATURE_ORDER]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Preprocesamiento del experimento 1
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]), CATEGORICAL_FEATURES),

            ("numeric", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
        ],
        remainder="drop",
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

    joblib.dump(model, models_dir / "vehicle_price_exp1.joblib") # Nombre distinto para cada experimento

    metrics = {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "r2": round(float(r2), 4),
        "features": FEATURE_ORDER,
        "target": TARGET,
        "model_type": "LinearRegression",
        "model_version": "v1",
    }

    # Nombre distinto para cada experimento
    with open(models_dir / "metrics-exp1.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Modelo y metricas guardados en models/")
    print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | R2: {r2:.4f}")


if __name__ == "__main__":
    train_and_save()
