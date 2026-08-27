"""Ejemplo BASICO de ETL: Extract -> Transform -> Load en un solo script.

Este ejemplo es INTENCIONALMENTE simple. No tiene:
- Capa de staging (no se conserva evidencia del dato crudo).
- Contrato de datos formal (las reglas estan hardcodeadas en el codigo).
- Cuarentena (los registros invalidos simplemente se descartan).
- Batch ID ni auditoria de la ejecucion.
- Idempotencia garantizada (cada corrida sobrescribe el archivo de salida
  completo, lo cual aqui es aceptable porque no hay carga incremental).

Sirve como punto de comparacion contra `ejemplo_2_etl_completo`.
"""

import logging
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
INPUT_PATH = PROJECT_DIR / "data" / "vehiculos_raw.csv"
OUTPUT_PATH = PROJECT_DIR / "data" / "vehiculos_clean.csv"
CURRENT_YEAR = 2026

BRAND_ALIASES = {
    "vw": "Volkswagen",
    "volkswagen": "Volkswagen",
    "nissan": "Nissan",
    "toyota": "Toyota",
    "mazda": "Mazda",
    "honda": "Honda",
}

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def extract(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    logging.info("EXTRACT: %s registros leidos de %s", len(df), path.name)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Homologacion de marca: mismos valores escritos de formas distintas.
    df["brand"] = df["brand"].str.strip().str.lower().map(BRAND_ALIASES).fillna(df["brand"])
    df["model"] = df["model"].astype(str).str.strip().str.title()

    # Reglas de validez basicas, aplicadas inline (sin contrato explicito).
    valid = (
        df["mileage"].notna()
        & (df["mileage"] >= 0)
        & df["price"].notna()
        & (df["price"] > 0)
        & df["year"].between(1990, CURRENT_YEAR)
    )
    rejected = (~valid).sum()
    df = df[valid].copy()

    df["vehicle_age"] = CURRENT_YEAR - df["year"]

    logging.info("TRANSFORM: %s registros validos, %s descartados (no se conservan)", len(df), rejected)
    return df


def load(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)
    logging.info("LOAD: %s registros escritos en %s (archivo sobrescrito por completo)", len(df), path.name)


def main() -> None:
    raw = extract(INPUT_PATH)
    clean = transform(raw)
    load(clean, OUTPUT_PATH)


if __name__ == "__main__":
    main()
