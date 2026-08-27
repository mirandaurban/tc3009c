#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ">>> 0) Instalando dependencias (pandas)"
pip install -q -r requirements.txt

echo ""
echo ">>> 1) Sembrando base fuente (data/vehicles.db)"
python seed_database.py

echo ""
echo ">>> 2) Primera corrida: bootstrap incremental (watermark inicial = 1900-01-01)"
python etl_completo.py

echo ""
echo ">>> 3) Segunda corrida sin cambios: debe procesar 0 vehiculos nuevos (incremental correcto)"
python etl_completo.py

echo ""
echo ">>> 4) Reset del watermark para simular un reprocesamiento del mismo batch (idempotencia)"
python -c "import json,pathlib; p=pathlib.Path('data/watermark_state.json'); p.write_text(json.dumps({'last_processed_updated_at': '1900-01-01T00:00:00'}, indent=2))"
python etl_completo.py

echo ""
echo ">>> 5) Verificacion: vehicles_curated debe seguir teniendo el mismo numero de filas que en la corrida 2"
python verify_etl.py
