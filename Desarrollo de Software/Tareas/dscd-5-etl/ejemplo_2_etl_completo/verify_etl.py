"""Consulta vehicles_curated, etl_quarantine y etl_runs para inspeccionar
el resultado del ETL completo."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent

with (PROJECT_DIR / "config.json").open(encoding="utf-8") as f:
    config = json.load(f)

db_path = PROJECT_DIR / config["database_path"]

with sqlite3.connect(db_path) as conn:
    print("\n=== vehicles_curated ===")
    print(pd.read_sql(f"SELECT * FROM {config['output_table']} ORDER BY vehicle_id", conn).to_string(index=False))

    print("\n=== etl_quarantine ===")
    try:
        print(pd.read_sql(f"SELECT * FROM {config['quarantine_table']}", conn).to_string(index=False))
    except pd.errors.DatabaseError:
        print("(tabla aun no existe)")

    print("\n=== etl_runs (auditoria) ===")
    print(
        pd.read_sql(f"SELECT * FROM {config['audit_table']} ORDER BY started_at", conn).to_string(index=False)
    )

print(f"\nWatermark actual: {json.load((PROJECT_DIR / config['watermark_path']).open(encoding='utf-8'))}")
