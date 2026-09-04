#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "====================================================="
echo "Examen: De Laboratorio a Pipeline de Datos Productivo"
echo "====================================================="
echo "Fecha: $(date)"
echo ""


echo ">>> 0) Instalando dependencias (pandas)"
pip install -q -r requirements.txt

echo ""
echo ">>> 1) Sembrando base fuente (data/vehicles.db)"
python scripts/seed_database.py
