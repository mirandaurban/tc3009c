#!/usr/bin/env bash
# Levanta el portal en http://127.0.0.1:5050
set -euo pipefail
cd "$(dirname "$0")"

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "No existe el entorno virtual. Ejecuta primero: ./setup.sh"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo ">>> Portal ETL disponible en http://127.0.0.1:5050"
python app.py
