"""
06_spark_sql.py

Objetivo: registrar una Temporary View y ejecutar la misma agregación
de la slide 13 mediante Spark SQL, mostrando su Execution Plan.

Ejecutar:
    python 06_spark_sql.py
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("06_spark_sql")
    .master("local[*]")
    .getOrCreate()
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/vehicles.csv")
)

# createOrReplaceTempView expone el DataFrame como una tabla temporal
# que puede consultarse con SQL dentro de la misma SparkSession.
df.createOrReplaceTempView("vehicles")

result = spark.sql("""
    SELECT
        brand,
        COUNT(*) AS vehicles,
        AVG(price) AS avg_price
    FROM vehicles
    WHERE year >= 2020
    GROUP BY brand
    ORDER BY avg_price DESC
""")

print("\n--- Resultado (Spark SQL) ---")
result.show(20)

# El mismo Catalyst Optimizer procesa tanto la ruta DataFrame como la
# ruta SQL: ambas terminan utilizando el mismo motor de ejecución.
print("\n--- Execution Plan ---")
result.explain("formatted")

spark.stop()
