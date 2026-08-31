"""
07_etl_pipeline.py

Objetivo: integrar en un solo pipeline las etapas READ, VALIDATE,
TRANSFORM, JOIN, AGGREGATE y WRITE, guardando el resultado curado en
formato Parquet particionado por año.

Ejecutar:
    python 07_etl_pipeline.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, count, avg, lit

spark = (
    SparkSession.builder
    .appName("07_etl_pipeline")
    .master("local[*]")
    .getOrCreate()
)

# ------------------------------------------------------------------
# READ
# ------------------------------------------------------------------
vehicles = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

manufacturers = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/manufacturers.csv")
)

original_count = vehicles.count()

# ------------------------------------------------------------------
# VALIDATE
# ------------------------------------------------------------------
# Reglas mínimas de calidad (Quality Gates) antes de escribir el
# resultado curado.
is_valid = (
    (col("price") > 0)
    & (col("year") >= 1990)
    & (col("year") <= 2026)
    & (col("mileage") >= 0)
)

valid = vehicles.filter(is_valid)
rejected = vehicles.filter(~is_valid)

valid_count = valid.count()
rejected_count = rejected.count()

# ------------------------------------------------------------------
# TRANSFORM
# ------------------------------------------------------------------
transformed = valid.withColumn("vehicle_age", lit(2026) - col("year"))

# ------------------------------------------------------------------
# JOIN
# ------------------------------------------------------------------
# manufacturers es pequeño: se envía una copia a cada Executor
# (Broadcast Join) para evitar un Shuffle sobre el lado grande.
joined = transformed.join(broadcast(manufacturers), "brand", "left")

# ------------------------------------------------------------------
# AGGREGATE
# ------------------------------------------------------------------
# Esta agregación es informativa (se muestra en consola); el dataset
# que se escribe es "joined", a nivel de registro individual.
summary = (
    joined
    .groupBy("brand")
    .agg(
        count("*").alias("vehicles"),
        avg("price").alias("avg_price"),
    )
    .orderBy(col("avg_price").desc())
)

print("\n--- Resumen por marca ---")
summary.show(20)

# ------------------------------------------------------------------
# WRITE
# ------------------------------------------------------------------
written_count = joined.count()

(
    joined
    .write
    .mode("overwrite")
    .partitionBy("year")
    .parquet("output/vehicles_curated")
)

# ------------------------------------------------------------------
# REPORTE FINAL
# ------------------------------------------------------------------
print("\n--- Reporte del pipeline ---")
print("Registros originales:", original_count)
print("Registros válidos:   ", valid_count)
print("Registros rechazados:", rejected_count)
print("Registros escritos:  ", written_count)
print("\nResultado guardado en: output/vehicles_curated (Parquet, particionado por year)")

spark.stop()
