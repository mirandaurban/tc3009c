"""
05_join.py

Objetivo: leer vehicles y manufacturers, realizar un JOIN normal y una
segunda variante utilizando Broadcast Join, y comparar el Execution
Plan de ambas.

Ejecutar:
    python 05_join.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

spark = (
    SparkSession.builder
    .appName("05_join")
    .master("local[*]")
    .getOrCreate()
)

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

print("Registros en vehicles:", vehicles.count())
print("Registros en manufacturers:", manufacturers.count())

# --- Variante 1: JOIN normal ---
# manufacturers es una tabla pequeña. Sin ninguna indicación, Spark
# puede decidir automáticamente la estrategia (en muchos casos ya
# aplica Broadcast por su tamaño gracias a la optimización por
# defecto), pero es importante entender la alternativa explícita.
result_join = vehicles.join(manufacturers, "brand", "left")

print("\n--- JOIN normal: muestra ---")
result_join.show(5)

print("\n--- JOIN normal: Execution Plan ---")
result_join.explain()

# --- Variante 2: Broadcast Join explícito ---
# Enviar una copia de manufacturers (tabla pequeña) a cada Executor
# permite completar el JOIN localmente en cada Partition del lado
# grande, evitando un Shuffle costoso sobre vehicles.
result_broadcast = vehicles.join(broadcast(manufacturers), "brand", "left")

print("\n--- Broadcast JOIN: muestra ---")
result_broadcast.show(5)

print("\n--- Broadcast JOIN: Execution Plan (buscar 'BroadcastExchange') ---")
result_broadcast.explain("formatted")

spark.stop()
