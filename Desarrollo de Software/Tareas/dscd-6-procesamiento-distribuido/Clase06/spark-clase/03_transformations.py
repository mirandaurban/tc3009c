"""
03_transformations.py

Objetivo: aplicar Transformations (filter, select, withColumn), mostrar
el resultado con una Action y observar el Execution Plan.

Ejecutar:
    python 03_transformations.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

spark = (
    SparkSession.builder
    .appName("03_transformations")
    .master("local[*]")
    .getOrCreate()
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

# Transformations: construyen una nueva representación lógica.
# Hasta aquí, Spark todavía no ejecuta nada (Lazy Evaluation).
recent = (
    df
    .filter(col("year") >= 2020)
    .select("brand", "year", "mileage", "price")
    .withColumn("vehicle_age", lit(2026) - col("year"))
)

# Action: solicita un resultado y provoca la ejecución.
print("\n--- recent.show() ---")
recent.show(10)

print("\nNúmero de registros filtrados (Action):", recent.count())

# Execution Plan: Logical Plan -> Catalyst -> Physical Plan.
print("\n--- recent.explain() ---")
recent.explain()

print("\n--- recent.explain('formatted') ---")
recent.explain("formatted")

spark.stop()
