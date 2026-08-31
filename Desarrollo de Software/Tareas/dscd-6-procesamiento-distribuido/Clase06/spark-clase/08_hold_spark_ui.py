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
