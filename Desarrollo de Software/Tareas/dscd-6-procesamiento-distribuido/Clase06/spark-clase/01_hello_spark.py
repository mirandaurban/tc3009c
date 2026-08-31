"""
01_hello_spark.py

Objetivo: crear la primera SparkSession, confirmar que Spark se ejecuta
localmente y detenerla correctamente.

Ejecutar:
    python 01_hello_spark.py
"""

from pyspark.sql import SparkSession

# SparkSession: punto principal de entrada para trabajar con
# DataFrames y Spark SQL.
spark = (
    SparkSession.builder
    .appName("ClaseSpark")
    # master("local[*]") ejecuta Spark localmente utilizando todos
    # los cores disponibles. No crea un clúster físico: todo continúa
    # ejecutándose en la misma computadora.
    .master("local[*]")
    .getOrCreate()
)

print("Spark version:", spark.version)
print("Master:", spark.sparkContext.master)
print("Cores disponibles (default parallelism):", spark.sparkContext.defaultParallelism)

# Detener la SparkSession libera los recursos del Driver y de los
# Executors locales. Siempre debe llamarse al finalizar la aplicación.
spark.stop()
