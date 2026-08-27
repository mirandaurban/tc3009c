#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ">>> 0) Instalando dependencias (duckdb)"
pip install -q -r requirements.txt

rm -f data/telco.duckdb data/customers_curated.parquet data/churn_by_segment_curated.parquet

echo ">>> 1) Primera corrida (full load) sobre el dataset real telco_churn.csv"
python etl_duckdb.py

echo ""
echo ">>> 2) Segunda corrida: full load es idempotente por reemplazo (CREATE OR REPLACE),"
echo "        no por UPSERT como en el ejemplo 2. customers_curated debe tener el mismo numero de filas."
python etl_duckdb.py

echo ""
echo ">>> 3) Verificacion"
python verify_etl.py
