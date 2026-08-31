"""
02_dataframe.py

Objetivo: leer vehicles.csv, mostrar datos, mostrar el schema inferido
y mostrar el número de Partitions con las que Spark representa el
DataFrame.

Ejecutar:
    python 02_dataframe.py
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("02_dataframe")
    .master("local[*]")
    .getOrCreate()
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

print("\n--- df.show() ---")
df.show(10)

print("\n--- df.printSchema() ---")
df.printSchema()

# Cada Partition puede procesarse como una unidad independiente de
# trabajo. Este número depende del tamaño del archivo, del número de
# cores locales y de la configuración de lectura.
print("\nNúmero de Partitions:", df.rdd.getNumPartitions())
print("Número de registros (Action):", df.count())

spark.stop()
