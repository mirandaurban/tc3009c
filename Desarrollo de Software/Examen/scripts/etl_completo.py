import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

"""
Generación del dataset
"""

@dataclass(frozen=True)
class ETLConfig:
    database_path: Path
    tarifas_path: Path
    catalogo_path: Path
    watermark_path: Path
    output_database: Path
    output_tables: Dict[str, str]
    quality_thresholds: Dict[str, float]
    current_year: int
    allowed_statuses: List[str]
    allowed_payment_methods: List[str]


def load_config() -> ETLConfig:
    with (PROJECT_DIR / "config.json").open(encoding="utf-8") as file:
        raw = json.load(file)
    return ETLConfig(
        database_path=PROJECT_DIR / raw["paths"]["database"],
        tarifas_path=PROJECT_DIR / raw["paths"]["tarifas"],
        catalogo_path=PROJECT_DIR / raw["paths"]["catalogo"],
        watermark_path=PROJECT_DIR / "data" / "watermark.json",
        output_database=PROJECT_DIR / "data" / "clinica_curated.db",
        output_tables={
            "dim_patients": "dim_patients",
            "dim_clinicas": "dim_clinicas",
            "dim_especialidades": "dim_especialidades",
            "fact_appointments": "fact_appointments",
            "dim_date": "dim_date",
        },
        quality_thresholds={
            "completeness_min": 0.70,
            "duplicate_rate_max": 0.05,
            "null_foreign_key_max": 0.10,
            "invalid_amount_max": 0.05,
        },
        current_year=2025,
        allowed_statuses=["completada", "no_show", "cancelada"],
        allowed_payment_methods=["efectivo", "tarjeta", "transferencia", "aseguradora"],
    )

def main() -> None:
    config = load_config()
    print(config)