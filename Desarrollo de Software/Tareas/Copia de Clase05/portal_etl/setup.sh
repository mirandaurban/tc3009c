#!/usr/bin/env bash
# Crea el entorno virtual del portal e instala todas las dependencias:
# las del portal (Flask) y las de los 3 ejemplos (pandas, duckdb).
set -euo pipefail
cd "$(dirname "$0")"

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo ">>> Creando entorno virtual en portal_etl/$VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo ">>> Instalando dependencias del portal"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ">>> Instalando dependencias de los 3 ejemplos"
pip install -q -r ../ejemplo_1_etl_basico/requirements.txt
pip install -q -r ../ejemplo_2_etl_completo/requirements.txt
pip install -q -r ../ejemplo_3_etl_duckdb/requirements.txt

echo ""
echo "Listo. Para levantar el portal ejecuta: ./start.sh"
