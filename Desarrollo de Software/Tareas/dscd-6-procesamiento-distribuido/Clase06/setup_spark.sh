#!/usr/bin/env bash
# =====================================================================
# setup_spark.sh
#
# Automatiza la habilitación de Apache Spark (PySpark) en local y deja
# lista una práctica completa sobre el caso de vehículos:
#
#   1. Verifica Python y Java (intenta instalarlos si faltan).
#   2. Crea la estructura del proyecto spark-clase/.
#   3. Crea y activa un entorno virtual.
#   4. Instala PySpark.
#   5. Genera los datos de práctica (vehicles.csv / manufacturers.csv).
#   6. Genera los 7 scripts de la práctica + 1 script de monitoreo.
#   7. Corre una prueba de humo (smoke test) para confirmar que Spark
#      funciona de verdad, no solo que "se instaló".
#   8. Deja un run_all.sh listo para ejecutar toda la práctica y un
#      reporte final con cómo verla, probarla y monitorearla.
#
# Uso:
#   chmod +x setup_spark.sh
#   ./setup_spark.sh                # crea ./spark-clase
#   ./setup_spark.sh /ruta/destino  # crea /ruta/destino
#
# Este script es idempotente: se puede volver a ejecutar sin romper
# nada; no sobrescribe datos ni venv si ya existen (salvo que se pida
# explícitamente con --force).
# =====================================================================

set -euo pipefail

# ---------------------------------------------------------------------
# 0. Configuración y utilidades
# ---------------------------------------------------------------------

PROJECT_DIR="${1:-./spark-clase}"
FORCE=0
for arg in "$@"; do
  [ "$arg" = "--force" ] && FORCE=1
done

PYSPARK_VERSION="3.5.1"
PYTHON_MIN_MINOR=9    # Python 3.9
PYTHON_MAX_MINOR=12   # Python 3.12
JAVA_MIN_MAJOR=11

if [ -t 1 ]; then
  C_RESET="\033[0m"; C_GREEN="\033[32m"; C_RED="\033[31m"
  C_YELLOW="\033[33m"; C_BLUE="\033[34m"; C_BOLD="\033[1m"
else
  C_RESET=""; C_GREEN=""; C_RED=""; C_YELLOW=""; C_BLUE=""; C_BOLD=""
fi

log_step() { printf "\n${C_BOLD}${C_BLUE}==> %s${C_RESET}\n" "$1"; }
log_ok()   { printf "${C_GREEN}  ✔ %s${C_RESET}\n" "$1"; }
log_warn() { printf "${C_YELLOW}  ! %s${C_RESET}\n" "$1"; }
log_err()  { printf "${C_RED}  ✘ %s${C_RESET}\n" "$1"; }
die()      { log_err "$1"; exit 1; }

trap 'log_err "El script falló en la línea $LINENO. Revisa el mensaje anterior."' ERR

OS_NAME="$(uname -s)"

# ---------------------------------------------------------------------
# 1. Verificar / instalar Python
# ---------------------------------------------------------------------

log_step "Paso 1/8 — Verificando Python"

if command -v python3 >/dev/null 2>&1; then
  PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  PY_MINOR="$(python3 -c 'import sys; print(sys.version_info[1])')"
  log_ok "Python detectado: $PY_VERSION ($(command -v python3))"
  if [ "$PY_MINOR" -lt "$PYTHON_MIN_MINOR" ] || [ "$PY_MINOR" -gt "$PYTHON_MAX_MINOR" ]; then
    log_warn "PySpark $PYSPARK_VERSION es más estable con Python 3.$PYTHON_MIN_MINOR–3.$PYTHON_MAX_MINOR. Se continúa, pero si falla la instalación, este es el primer sospechoso."
  fi
else
  log_warn "Python 3 no encontrado. Intentando instalar..."
  if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew install python@3.11
  elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  else
    die "No se pudo instalar Python automáticamente. Instálalo manualmente desde https://www.python.org/downloads/ y vuelve a correr este script."
  fi
  command -v python3 >/dev/null 2>&1 || die "Python sigue sin encontrarse tras el intento de instalación."
  log_ok "Python instalado: $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
fi

# ---------------------------------------------------------------------
# 2. Verificar / instalar Java
# ---------------------------------------------------------------------

log_step "Paso 2/8 — Verificando Java (Spark corre sobre la JVM)"

if command -v java >/dev/null 2>&1; then
  JAVA_VERSION_RAW="$(java -version 2>&1 | head -1)"
  log_ok "Java detectado: $JAVA_VERSION_RAW"
  JAVA_MAJOR="$(java -version 2>&1 | head -1 | grep -oE '"[0-9]+' | tr -d '"' | head -1)"
  if [ -n "${JAVA_MAJOR:-}" ] && [ "$JAVA_MAJOR" -lt "$JAVA_MIN_MAJOR" ] 2>/dev/null; then
    log_warn "Java $JAVA_MAJOR detectado; se recomienda 11 o 17 para Spark $PYSPARK_VERSION."
  fi
else
  log_warn "Java no encontrado. Intentando instalar OpenJDK 17..."
  if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew install openjdk@17
    export PATH="/usr/local/opt/openjdk@17/bin:$PATH"
  elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y openjdk-17-jdk
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y java-17-openjdk
  else
    die "No se pudo instalar Java automáticamente. Instala un JDK 11 o 17 manualmente y vuelve a correr este script."
  fi
  command -v java >/dev/null 2>&1 || die "Java sigue sin encontrarse tras el intento de instalación."
  log_ok "Java instalado: $(java -version 2>&1 | head -1)"
fi

# ---------------------------------------------------------------------
# 3. Crear estructura del proyecto
# ---------------------------------------------------------------------

log_step "Paso 3/8 — Creando estructura del proyecto en: $PROJECT_DIR"

mkdir -p "$PROJECT_DIR"/data "$PROJECT_DIR"/output "$PROJECT_DIR"/logs
cd "$PROJECT_DIR"
PROJECT_DIR="$(pwd)"
log_ok "Directorio del proyecto: $PROJECT_DIR"

# ---------------------------------------------------------------------
# 4. Crear y poblar el entorno virtual
# ---------------------------------------------------------------------

log_step "Paso 4/8 — Preparando entorno virtual (.venv) e instalando PySpark $PYSPARK_VERSION"

if [ -d ".venv" ] && [ "$FORCE" -eq 0 ]; then
  log_warn ".venv ya existe, se reutiliza (usa --force para recrearlo)."
else
  [ -d ".venv" ] && rm -rf ".venv"
  python3 -m venv .venv
  log_ok "Entorno virtual creado."
fi

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

"$VENV_PIP" install --upgrade pip --quiet
echo "pyspark==${PYSPARK_VERSION}" > requirements.txt
"$VENV_PIP" install -r requirements.txt --quiet
INSTALLED_VERSION="$("$VENV_PY" -c 'import pyspark; print(pyspark.__version__)')"
log_ok "PySpark instalado dentro de .venv: versión $INSTALLED_VERSION"

# ---------------------------------------------------------------------
# 5. Generar los datos de práctica (si no existen o --force)
# ---------------------------------------------------------------------

log_step "Paso 5/8 — Generando datos de práctica (caso vehículos)"

if [ -f "data/vehicles.csv" ] && [ "$FORCE" -eq 0 ]; then
  log_warn "data/vehicles.csv ya existe, se conserva (usa --force para regenerar)."
else
  "$VENV_PY" - << 'PYEOF'
import random
random.seed(42)

brands = ["Toyota", "Nissan", "BMW", "Mazda", "Volkswagen", "Ferrari", "Honda", "Chevrolet", "Hyundai", "Kia"]
# Distribución desigual a propósito: sirve para observar Data Skew más adelante.
weights = [28, 22, 8, 10, 18, 1, 6, 4, 2, 1]

base_price = {
    "Toyota": 320000, "Nissan": 260000, "BMW": 650000, "Mazda": 300000,
    "Volkswagen": 280000, "Ferrari": 3800000, "Honda": 290000,
    "Chevrolet": 270000, "Hyundai": 250000, "Kia": 240000,
}

rows = []
vehicle_id = 1
for brand, w in zip(brands, weights):
    for _ in range(w * 20):
        year = random.randint(2015, 2024)
        mileage = random.randint(1000, 150000)
        price = int(base_price[brand] * (1 - (2024 - year) * 0.05) * random.uniform(0.85, 1.15))
        price = max(price, 50000)
        rows.append((vehicle_id, brand, year, mileage, price))
        vehicle_id += 1

random.shuffle(rows)

with open("data/vehicles.csv", "w") as f:
    f.write("vehicle_id,brand,year,mileage,price\n")
    for r in rows:
        f.write(",".join(str(x) for x in r) + "\n")

# Cinco registros inválidos a propósito, para ejercitar los Quality Gates.
with open("data/vehicles.csv", "a") as f:
    f.write("9001,Toyota,2028,45000,320000\n")   # year fuera de rango
    f.write("9002,Nissan,2019,-500,180000\n")     # mileage negativo
    f.write("9003,BMW,1985,60000,400000\n")       # year fuera de rango
    f.write("9004,Mazda,2021,50000,-100\n")       # price negativo
    f.write("9005,Kia,2022,30000,0\n")            # price en cero

manufacturers = [
    ("Toyota", "Japan", 1937), ("Nissan", "Japan", 1933), ("BMW", "Germany", 1916),
    ("Mazda", "Japan", 1920), ("Volkswagen", "Germany", 1937), ("Ferrari", "Italy", 1939),
    ("Honda", "Japan", 1948), ("Chevrolet", "USA", 1911), ("Hyundai", "South Korea", 1967),
    ("Kia", "South Korea", 1944),
]
with open("data/manufacturers.csv", "w") as f:
    f.write("brand,country,founded\n")
    for m in manufacturers:
        f.write(",".join(str(x) for x in m) + "\n")

print(f"vehicles.csv: {len(rows) + 5} filas (5 inválidas a propósito)")
print("manufacturers.csv: 10 filas")
PYEOF
  log_ok "Datos generados en data/vehicles.csv y data/manufacturers.csv"
fi

# ---------------------------------------------------------------------
# 6. Generar los scripts de la práctica
# ---------------------------------------------------------------------

log_step "Paso 6/8 — Generando los scripts de la práctica"

write_script() {
  local path="$1"
  if [ -f "$path" ] && [ "$FORCE" -eq 0 ]; then
    log_warn "$path ya existe, se conserva (usa --force para regenerar)."
    return 0
  fi
  cat > "$path"
}

write_script "01_hello_spark.py" << 'PYEOF'
"""01_hello_spark.py — primera SparkSession."""
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("ClaseSpark")
    .master("local[*]")
    .getOrCreate()
)

print("Spark version:", spark.version)
print("Master:", spark.sparkContext.master)
print("Cores disponibles:", spark.sparkContext.defaultParallelism)

spark.stop()
PYEOF

write_script "02_dataframe.py" << 'PYEOF'
"""02_dataframe.py — lectura y exploración del DataFrame."""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("02_dataframe").master("local[*]").getOrCreate()

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

df.show(10)
df.printSchema()
print("Número de Partitions:", df.rdd.getNumPartitions())
print("Número de registros:", df.count())

spark.stop()
PYEOF

write_script "03_transformations.py" << 'PYEOF'
"""03_transformations.py — Transformations, Actions, Execution Plan."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

spark = SparkSession.builder.appName("03_transformations").master("local[*]").getOrCreate()

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

recent = (
    df.filter(col("year") >= 2020)
      .select("brand", "year", "mileage", "price")
      .withColumn("vehicle_age", lit(2026) - col("year"))
)

recent.show(10)
print("Registros filtrados:", recent.count())
recent.explain("formatted")

spark.stop()
PYEOF

write_script "04_aggregations.py" << 'PYEOF'
"""04_aggregations.py — agregaciones y aparición del Shuffle (Exchange)."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg

spark = SparkSession.builder.appName("04_aggregations").master("local[*]").getOrCreate()

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

agg = (
    df.groupBy("brand")
      .agg(count("*").alias("vehicles"), avg("price").alias("avg_price"))
      .orderBy(col("avg_price").desc())
)

agg.show(20)
agg.explain()  # buscar "Exchange" en el plan

spark.stop()
PYEOF

write_script "05_join.py" << 'PYEOF'
"""05_join.py — JOIN normal vs. Broadcast Join."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

spark = SparkSession.builder.appName("05_join").master("local[*]").getOrCreate()

vehicles = spark.read.option("header", True).option("inferSchema", True).csv("data/vehicles.csv")
manufacturers = spark.read.option("header", True).option("inferSchema", True).csv("data/manufacturers.csv")

result = vehicles.join(manufacturers, "brand", "left")
result.show(5)
result.explain()

result_bc = vehicles.join(broadcast(manufacturers), "brand", "left")
result_bc.show(5)
result_bc.explain("formatted")  # buscar "BroadcastExchange"

spark.stop()
PYEOF

write_script "06_spark_sql.py" << 'PYEOF'
"""06_spark_sql.py — la misma lógica expresada en Spark SQL."""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("06_spark_sql").master("local[*]").getOrCreate()

df = spark.read.option("header", True).option("inferSchema", True).csv("data/vehicles.csv")
df.createOrReplaceTempView("vehicles")

result = spark.sql("""
    SELECT brand, COUNT(*) AS vehicles, AVG(price) AS avg_price
    FROM vehicles
    WHERE year >= 2020
    GROUP BY brand
    ORDER BY avg_price DESC
""")

result.show(20)
result.explain("formatted")

spark.stop()
PYEOF

write_script "07_etl_pipeline.py" << 'PYEOF'
"""07_etl_pipeline.py — pipeline ETL completo: READ, VALIDATE, TRANSFORM, JOIN, AGGREGATE, WRITE."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, count, avg, lit

spark = SparkSession.builder.appName("07_etl_pipeline").master("local[*]").getOrCreate()

vehicles = spark.read.option("header", True).option("inferSchema", True).csv("data/vehicles.csv")
manufacturers = spark.read.option("header", True).option("inferSchema", True).csv("data/manufacturers.csv")

original_count = vehicles.count()

is_valid = (
    (col("price") > 0)
    & (col("year") >= 1990)
    & (col("year") <= 2026)
    & (col("mileage") >= 0)
)
valid = vehicles.filter(is_valid)
rejected = vehicles.filter(~is_valid)

transformed = valid.withColumn("vehicle_age", lit(2026) - col("year"))
curated = transformed.join(broadcast(manufacturers), "brand", "left")

summary = (
    curated.groupBy("brand")
    .agg(count("*").alias("vehicles"), avg("price").alias("avg_price"))
    .orderBy(col("avg_price").desc())
)
print("\n--- Resumen por marca ---")
summary.show(20)

written_count = curated.count()
curated.write.mode("overwrite").partitionBy("year").parquet("output/vehicles_curated")

print("\n--- Reporte del pipeline ---")
print("Registros originales:", original_count)
print("Registros válidos:   ", valid.count())
print("Registros rechazados:", rejected.count())
print("Registros escritos:  ", written_count)
print("\nResultado guardado en: output/vehicles_curated (Parquet, particionado por year)")

spark.stop()
PYEOF

write_script "08_hold_spark_ui.py" << 'PYEOF'
"""
08_hold_spark_ui.py — igual que el pipeline ETL, pero se detiene ANTES
de cerrar Spark para poder inspeccionar Spark UI con calma.

Uso:
    python 08_hold_spark_ui.py
    Abrir http://localhost:4040 mientras el script espera.
    Presionar Enter en la terminal para cerrar Spark y terminar.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, lit

spark = SparkSession.builder.appName("08_hold_spark_ui").master("local[*]").getOrCreate()

ui_url = spark.sparkContext.uiWebUrl
print(f"\nSpark UI disponible en: {ui_url}\n", flush=True)

vehicles = spark.read.option("header", True).option("inferSchema", True).csv("data/vehicles.csv")
manufacturers = spark.read.option("header", True).option("inferSchema", True).csv("data/manufacturers.csv")

is_valid = (col("price") > 0) & (col("year") >= 1990) & (col("year") <= 2026) & (col("mileage") >= 0)
valid = vehicles.filter(is_valid)
transformed = valid.withColumn("vehicle_age", lit(2026) - col("year"))
curated = transformed.join(broadcast(manufacturers), "brand", "left")

curated.write.mode("overwrite").partitionBy("year").parquet("output/vehicles_curated_hold")
print("Pipeline ejecutado. Registros escritos:", curated.count(), flush=True)

print(f"\nAbre {ui_url} y revisa las pestañas Jobs, Stages y SQL/DataFrame.", flush=True)
input("\nPresiona Enter aquí para cerrar Spark UI y finalizar...\n")

spark.stop()
PYEOF

log_ok "8 scripts generados (01 a 07 de práctica + 08 de monitoreo)."

# ---------------------------------------------------------------------
# 7. Prueba de humo (smoke test): confirmar que Spark funciona de verdad
# ---------------------------------------------------------------------

log_step "Paso 7/8 — Probando que Spark funciona (smoke test)"

SMOKE_LOG="logs/00_smoke_test.log"
if "$VENV_PY" 01_hello_spark.py > "$SMOKE_LOG" 2>&1; then
  if grep -q "Spark version:" "$SMOKE_LOG"; then
    log_ok "Smoke test exitoso. Detalle:"
    grep -E "Spark version:|Master:|Cores disponibles:" "$SMOKE_LOG" | sed 's/^/    /'
  else
    die "El script corrió pero no se encontró la salida esperada. Ver $PROJECT_DIR/$SMOKE_LOG"
  fi
else
  log_err "El smoke test falló. Últimas líneas del log:"
  tail -20 "$SMOKE_LOG" | sed 's/^/    /'
  die "Revisa $PROJECT_DIR/$SMOKE_LOG para el detalle completo."
fi

# ---------------------------------------------------------------------
# 8. Generar run_all.sh (ejecuta toda la práctica y valida resultados)
# ---------------------------------------------------------------------

log_step "Paso 8/8 — Generando run_all.sh"

cat > run_all.sh << 'RUNEOF'
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
RUNEOF

chmod +x run_all.sh
log_ok "run_all.sh generado y marcado como ejecutable."

# ---------------------------------------------------------------------
# Reporte final
# ---------------------------------------------------------------------

printf "\n${C_BOLD}${C_GREEN}Spark quedó habilitado y la práctica está lista.${C_RESET}\n\n"

cat << REPORT
Proyecto:        $PROJECT_DIR
PySpark:         $INSTALLED_VERSION
Entorno virtual: $PROJECT_DIR/.venv

Cómo ejecutar un paso individual:
  cd "$PROJECT_DIR"
  source .venv/bin/activate
  python 02_dataframe.py

Cómo ejecutar TODA la práctica de una vez (con verificación automática):
  cd "$PROJECT_DIR"
  ./run_all.sh

Cómo VER y MONITOREAR una ejecución en vivo (Spark UI):
  1. En una terminal, ejecutar un script que tarde lo suficiente, por ejemplo:
       source .venv/bin/activate
       python 08_hold_spark_ui.py
     (si vas a redirigir la salida a un archivo en vez de verla en la
     terminal, usa "python -u 08_hold_spark_ui.py" para evitar que el
     buffering de Python retrase lo que ves en el log)
  2. Mientras el script espera (verás el mensaje "Presiona Enter..."),
     abrir en el navegador:
       http://localhost:4040
  3. Revisar las pestañas:
       - Jobs:            cuántos Jobs se generaron y su duración.
       - Stages:          cuántas Tasks tiene cada Stage y si hubo
                          Shuffle Read/Write.
       - SQL/DataFrame:   el Execution Plan de forma gráfica.
       - Executors:       memoria y cores usados localmente.
  4. Regresar a la terminal y presionar Enter para cerrar Spark.

Cómo confirmar que Spark UI está activo desde la terminal (opcional):
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4040
  (200 = activo; si no responde, revisar la consola del script por el
   puerto real, ya que Spark usa 4041, 4042... si 4040 está ocupado)

Cómo saber si un proceso de Spark quedó "vivo" sin querer:
  ps aux | grep SparkSubmit
  lsof -i :4040

Logs de cada ejecución (generados por run_all.sh):
  $PROJECT_DIR/logs/*.log

Para forzar una reinstalación completa (venv, datos y scripts):
  ./setup_spark.sh "$PROJECT_DIR" --force
REPORT
