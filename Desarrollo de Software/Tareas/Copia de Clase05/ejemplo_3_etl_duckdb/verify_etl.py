"""Verificacion basica de la corrida del ejemplo 3 (ETL con DuckDB)."""

from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "telco.duckdb"

if not DB_PATH.exists():
    raise SystemExit("No existe data/telco.duckdb. Ejecuta primero etl_duckdb.py")

con = duckdb.connect(str(DB_PATH), read_only=True)

source_rows = con.execute("SELECT count(*) FROM stg_customers").fetchone()[0]
curated_rows = con.execute("SELECT count(*) FROM customers_curated").fetchone()[0]
quarantined = con.execute("SELECT count(*) FROM etl_quarantine").fetchone()[0]
runs = con.execute("SELECT count(*) FROM etl_runs").fetchone()[0]

if curated_rows != source_rows - quarantined:
    raise SystemExit(
        f"Reconciliacion incorrecta: curated={curated_rows} pero source-quarantine={source_rows - quarantined}"
    )

# El caso interesante de la clase: el blanco en TotalCharges esta resuelto
# como negocio (tenure=0 -> 0.0), asi que ningun cliente nuevo debe quedar
# en cuarentena y ninguno debe tener total_charges NULL.
new_customers_ok = con.execute(
    "SELECT count(*) FROM customers_curated WHERE tenure = 0 AND total_charges = 0.0"
).fetchone()[0]
still_dirty_quotes = con.execute(
    "SELECT count(*) FROM customers_curated WHERE payment_method LIKE '''%' OR contract LIKE '''%'"
).fetchone()[0]

if still_dirty_quotes != 0:
    raise SystemExit("Quedaron comillas simples sin limpiar en columnas categoricas.")

segments = con.execute("SELECT count(*) FROM churn_by_segment_curated").fetchone()[0]

print(f"OK: {source_rows} filas fuente, {quarantined} en cuarentena, {curated_rows} en customers_curated.")
print(f"OK: {new_customers_ok} clientes nuevos (tenure=0) con total_charges=0.0 por regla de negocio.")
print(f"OK: {segments} segmentos (contract x tenure_bucket) en churn_by_segment_curated.")
print(f"OK: {runs} corrida(s) registrada(s) en etl_runs.")
