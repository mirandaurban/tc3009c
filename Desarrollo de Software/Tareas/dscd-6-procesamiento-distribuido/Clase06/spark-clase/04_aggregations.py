"""
04_aggregations.py

Objetivo: agrupar por marca, calcular count y average price, y ubicar
dónde puede aparecer un Shuffle en el plan de ejecución.

Ejecutar:
    python 04_aggregations.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg

spark = (
    SparkSession.builder
    .appName("04_aggregations")
    .master("local[*]")
    .getOrCreate()
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

# groupBy() es una Wide Transformation: requiere datos de múltiples
# Partitions para calcular el resultado por cada valor de "brand".
# Esto puede producir un Shuffle: Spark redistribuye los registros
# entre Partitions/Executors de modo que todos los registros de una
# misma marca terminen juntos antes de agregarlos.
agg = (
    df
    .groupBy("brand")
    .agg(
        count("*").alias("vehicles"),
        avg("price").alias("avg_price"),
    )
    .orderBy(col("avg_price").desc())
)

print("\n--- Resultado agregado ---")
agg.show(20)

# En el Physical Plan de una agregación como esta suele aparecer un
# "Exchange" (el operador físico detrás del Shuffle) entre el scan y
# la agregación final.
print("\n--- Execution Plan (buscar 'Exchange' = Shuffle) ---")
agg.explain()

spark.stop()
