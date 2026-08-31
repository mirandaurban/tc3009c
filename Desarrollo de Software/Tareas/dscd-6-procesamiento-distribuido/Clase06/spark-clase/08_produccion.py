"""
08_produccion.py

Objetivo: cerrar la práctica con buenas prácticas de producción sobre
el mismo caso conductor (vehicles.csv):

  - Configuración explícita de Adaptive Query Execution (AQE) y del
    número de particiones de shuffle en el builder de SparkSession.
  - Lectura tolerante a datos corruptos (modo PERMISSIVE) con una
    columna aparte para los registros que no calzan con el esquema,
    conectando con los Quality Gates de 07_etl_pipeline.py.
  - Reglas de validación separadas en una función pura (validar_reglas),
    con un mini "test" manual al final del script que ilustra el
    patrón de testing descrito en la slide de Testing, sin necesitar
    pytest instalado.
  - Escritura idempotente usando overwrite dinámico por partición.
  - Un reporte final de ejecución, igual que 07_etl_pipeline.py.

Ejecutar:
    python 08_produccion.py
"""

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, lit
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType
)

# ------------------------------------------------------------------
# SPARKSESSION: configuración explícita de recursos y AQE
# ------------------------------------------------------------------
# spark.sql.adaptive.enabled: activa Adaptive Query Execution (AQE).
#   AQE observa estadísticas reales durante la ejecución (no solo
#   estimaciones del plan) y puede: coalescer particiones de shuffle
#   demasiado pequeñas, y dividir/replanificar particiones afectadas
#   por Data Skew, sin que el desarrollador lo controle manualmente.
#   Es la técnica que la slide "Dos problemas de distribución" dejó
#   mencionada como "sin desarrollar".
#
# spark.sql.shuffle.partitions: número de particiones que se crean
#   tras una operación con Shuffle (groupBy, join con shuffle, etc.).
#   El valor por defecto de Spark (200) suele ser excesivo para un
#   dataset pequeño en local[*]; aquí se reduce explícitamente. Con
#   AQE activo, este valor es solo un punto de partida: Spark puede
#   coalescer particiones vecinas si resultan demasiado pequeñas.
spark = (
    SparkSession.builder
    .appName("08_produccion")
    .master("local[*]")
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

# ------------------------------------------------------------------
# READ (modo PERMISSIVE explícito + columna de registros corruptos)
# ------------------------------------------------------------------
# mode="PERMISSIVE" es el modo por defecto de Spark al leer CSV/JSON,
# pero aquí se declara explícitamente junto con
# columnNameOfCorruptRecord: cualquier fila que no calce con el
# esquema declarado (tipo inválido, columnas de más, etc.) no
# revienta el job ni se descarta en silencio; se guarda completa en
# la columna "_corrupt_record" para poder inspeccionarla.
#
# Nota: columnNameOfCorruptRecord solo funciona si se declara un
# schema explícito (no con inferSchema=True), por eso aquí se define
# el StructType a mano.
vehicles_schema = StructType([
    StructField("vehicle_id", IntegerType(), True),
    StructField("brand", StringType(), True),
    StructField("year", IntegerType(), True),
    StructField("mileage", IntegerType(), True),
    StructField("price", DoubleType(), True),
    StructField("_corrupt_record", StringType(), True),
])

vehicles_raw = (
    spark.read
    .option("header", True)
    .option("mode", "PERMISSIVE")
    .option("columnNameOfCorruptRecord", "_corrupt_record")
    .schema(vehicles_schema)
    .csv("data/vehicles.csv")
)

original_count = vehicles_raw.count()

corrupt = vehicles_raw.filter(col("_corrupt_record").isNotNull())
corrupt_count = corrupt.count()

vehicles = vehicles_raw.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
readable_count = vehicles.count()

print("\n--- Lectura con manejo de datos corruptos ---")
print("Registros leídos:          ", original_count)
print("Registros corruptos (modo PERMISSIVE, capturados aparte):", corrupt_count)
print("Registros utilizables:     ", readable_count)


# ------------------------------------------------------------------
# QUALITY GATES como función pura (mismo criterio que 07_etl_pipeline.py)
# ------------------------------------------------------------------
def validar_reglas(df):
    """Aplica las reglas de Quality Gates de 07_etl_pipeline.py.

    Función pura: no lee archivos, no imprime nada, no depende de una
    SparkSession global más allá del DataFrame recibido como
    argumento. Esto permite probarla de forma aislada, con un
    DataFrame construido en memoria, sin necesitar vehicles.csv.

    Retorna una tupla (validos, invalidos) con dos DataFrames.
    """
    is_valid = (
        (col("price") > 0)
        & (col("year") >= 1990)
        & (col("year") <= 2026)
        & (col("mileage") >= 0)
    )
    return df.filter(is_valid), df.filter(~is_valid)


valid, rejected = validar_reglas(vehicles)
valid_count = valid.count()
rejected_count = rejected.count()

# ------------------------------------------------------------------
# TRANSFORM
# ------------------------------------------------------------------
transformed = valid.withColumn("vehicle_age", lit(2026) - col("year"))

# ------------------------------------------------------------------
# WRITE (idempotente): overwrite dinámico por partición
# ------------------------------------------------------------------
# .mode("overwrite") por sí solo, junto con partitionBy(), reemplaza
# TODO el directorio de salida (todas las particiones existentes),
# aunque el DataFrame que se escribe solo contenga algunos valores de
# "year". Esto es seguro pero caro: se pierde el histórico de años
# que no vinieron en esta corrida.
#
# spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
# cambia ese comportamiento: con overwrite + partitionBy, Spark borra
# y reescribe ÚNICAMENTE las particiones (carpetas year=YYYY) que
# están presentes en el DataFrame actual, dejando el resto del
# histórico intacto. Es lo que hace que reejecutar el mismo job dos
# veces con el mismo insumo produzca el mismo resultado (idempotencia)
# sin borrar particiones de otras corridas.
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

written_count = transformed.count()

(
    transformed
    .write
    .mode("overwrite")
    .partitionBy("year")
    .parquet("output/vehicles_produccion")
)

# ------------------------------------------------------------------
# REPORTE FINAL
# ------------------------------------------------------------------
print("\n--- Reporte de ejecución (08_produccion.py) ---")
print("Registros leídos:      ", original_count)
print("Registros corruptos:   ", corrupt_count)
print("Registros válidos:     ", valid_count)
print("Registros rechazados:  ", rejected_count)
print("Registros escritos:    ", written_count)
print("AQE habilitado:        ", spark.conf.get("spark.sql.adaptive.enabled"))
print("Shuffle partitions:    ", spark.conf.get("spark.sql.shuffle.partitions"))
print("partitionOverwriteMode:", spark.conf.get("spark.sql.sources.partitionOverwriteMode"))
print("\nResultado guardado en: output/vehicles_produccion (Parquet, particionado por year, overwrite dinámico)")

spark.stop()


# ----------------------------------------------------------------------
# MINI "TEST" MANUAL (patrón de testing sin pytest)
# ----------------------------------------------------------------------
# Esto ilustra, sin depender de pytest ni de archivos reales, la idea
# central de la slide de Testing: crear una SparkSession de prueba,
# construir un DataFrame pequeño y conocido en memoria, y comparar el
# resultado real contra el esperado con un simple assert.
#
# En un proyecto real esto viviría en test_produccion.py, con pytest y
# una fixture de sesión (scope="session") en conftest.py en lugar del
# bloque __main__ de aquí abajo.
if __name__ == "__main__":
    test_spark = (
        SparkSession.builder
        .appName("08_produccion_test")
        .master("local[*]")
        .getOrCreate()
    )

    casos = [
        # Caso válido: year, mileage y price dentro de rango.
        Row(vehicle_id=1, brand="Toyota", year=2022, mileage=45000, price=385000.0),
        # Caso inválido: price <= 0.
        Row(vehicle_id=2, brand="Nissan", year=2020, mileage=72000, price=0.0),
    ]
    df_prueba = test_spark.createDataFrame(casos)

    validos, invalidos = validar_reglas(df_prueba)

    assert validos.count() == 1, "Se esperaba exactamente 1 registro válido"
    assert invalidos.count() == 1, "Se esperaba exactamente 1 registro inválido"
    assert validos.first()["vehicle_id"] == 1, "El registro válido debía ser vehicle_id=1"
    assert invalidos.first()["vehicle_id"] == 2, "El registro inválido debía ser vehicle_id=2"

    print("\n--- Mini test manual de validar_reglas() ---")
    print("OK: 1 registro válido, 1 registro inválido, tal como se esperaba.")

    test_spark.stop()
