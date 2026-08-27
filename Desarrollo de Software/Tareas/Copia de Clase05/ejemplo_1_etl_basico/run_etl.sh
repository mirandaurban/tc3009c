#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ">>> 0) Instalando dependencias (pandas)"
pip install -q -r requirements.txt

echo ""
echo ">>> 1) Corriendo el ETL basico (Extract -> Transform -> Load, sin staging ni auditoria)"
python etl_basico.py

echo ""
echo ">>> 2) Resultado"
wc -l data/vehiculos_clean.csv
