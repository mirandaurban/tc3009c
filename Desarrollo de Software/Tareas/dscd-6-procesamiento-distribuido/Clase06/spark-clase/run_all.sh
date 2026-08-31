#!/usr/bin/env bash
# Ejecuta toda la práctica en orden (02 a 07), guarda un log por script
# en logs/, y al final imprime un resumen PASS/FAIL + verificaciones
# de contenido específicas de cada paso (Partitions, Exchange,
# BroadcastExchange, carpeta de salida particionada).
set -uo pipefail
cd "$(dirname "$0")"

VENV_PY=".venv/bin/python"
mkdir -p logs

declare -a SCRIPTS=(
  "02_dataframe.py"
  "03_transformations.py"
  "04_aggregations.py"
  "05_join.py"
  "06_spark_sql.py"
  "07_etl_pipeline.py"
)

PASS=0
FAIL=0

echo "Ejecutando la práctica completa..."
echo

for script in "${SCRIPTS[@]}"; do
  log_file="logs/${script%.py}.log"
  printf "  %-28s ... " "$script"
  if "$VENV_PY" "$script" > "$log_file" 2>&1; then
    printf "OK\n"
    PASS=$((PASS + 1))
  else
    printf "FALLÓ (ver %s)\n" "$log_file"
    FAIL=$((FAIL + 1))
  fi
done

echo
echo "--- Verificaciones de contenido ---"

check() {
  local desc="$1" file="$2" pattern="$3"
  if grep -q "$pattern" "$file" 2>/dev/null; then
    echo "  ✔ $desc"
  else
    echo "  ✘ $desc (no se encontró '$pattern' en $file)"
  fi
}

check "04: aparece Shuffle (Exchange) en el plan"        "logs/04_aggregations.log"    "Exchange"
check "05: aparece Broadcast Join en el plan"            "logs/05_join.log"            "Broadcast"
check "06: Spark SQL produjo resultados"                 "logs/06_spark_sql.log"       "avg_price"
check "07: el pipeline reportó registros escritos"       "logs/07_etl_pipeline.log"    "Registros escritos"

if [ -d "output/vehicles_curated" ]; then
  n_partitions=$(find output/vehicles_curated -maxdepth 1 -type d -name "year=*" | wc -l | tr -d ' ')
  echo "  ✔ 07: output/vehicles_curated/ generado con $n_partitions particiones por year"
else
  echo "  ✘ 07: no se encontró output/vehicles_curated/"
fi

echo
echo "--- Resumen ---"
echo "  Scripts OK:     $PASS"
echo "  Scripts FALLÓ:  $FAIL"

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "Todo corrió correctamente. Revisa los logs en logs/ para el detalle de cada Execution Plan."
  exit 0
else
  echo
  echo "Hay scripts que fallaron. Revisa los logs correspondientes en logs/."
  exit 1
fi
