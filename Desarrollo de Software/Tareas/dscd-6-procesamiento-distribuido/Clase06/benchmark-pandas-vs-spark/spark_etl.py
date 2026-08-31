"""
spark_etl.py — el mismo pipeline ETL de la práctica (07_etl_pipeline.py),
parametrizado y con medición de tiempo por etapa para comparar contra
pandas_etl.py en igualdad de condiciones.

Uso:
    python spark_etl.py --data-dir data --out-dir output_spark
"""
import argparse
import os
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, col, count, avg, lit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="output_spark")
    ap.add_argument("--master", default="local[*]")
    args = ap.parse_args()

    t0 = time.perf_counter()
    spark = SparkSession.builder.appName("benchmark_etl").master(args.master).getOrCreate()

    t_read0 = time.perf_counter()
    vehicles = spark.read.option("header", True).option("inferSchema", True) \
        .csv(os.path.join(args.data_dir, "vehicles.csv"))
    manufacturers = spark.read.option("header", True).option("inferSchema", True) \
        .csv(os.path.join(args.data_dir, "manufacturers.csv"))
    original_count = vehicles.count()  # fuerza la lectura real (evaluación perezosa)
    t_read = time.perf_counter() - t_read0

    t_val0 = time.perf_counter()
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
    t_val = time.perf_counter() - t_val0

    t_tr0 = time.perf_counter()
    transformed = valid.withColumn("vehicle_age", lit(2026) - col("year"))
    t_tr = time.perf_counter() - t_tr0

    t_join0 = time.perf_counter()
    curated = transformed.join(broadcast(manufacturers), "brand", "left")
    t_join = time.perf_counter() - t_join0

    t_agg0 = time.perf_counter()
    summary = (
        curated.groupBy("brand")
        .agg(count("*").alias("vehicles"), avg("price").alias("avg_price"))
        .orderBy(col("avg_price").desc())
    )
    print("\n--- Resumen por marca ---")
    summary.show(20)
    t_agg = time.perf_counter() - t_agg0

    t_write0 = time.perf_counter()
    written_count = curated.count()
    curated.write.mode("overwrite").partitionBy("year").parquet(
        os.path.join(args.out_dir, "vehicles_curated")
    )
    t_write = time.perf_counter() - t_write0

    total = time.perf_counter() - t0

    print("\n--- Reporte del pipeline (Spark) ---")
    print("Registros originales:", original_count)
    print("Registros válidos:   ", valid_count)
    print("Registros rechazados:", rejected_count)
    print("Registros escritos:  ", written_count)
    print(f"\nTiempo lectura:       {t_read:.2f} s")
    print(f"Tiempo validación:    {t_val:.2f} s")
    print(f"Tiempo transformación:{t_tr:.2f} s")
    print(f"Tiempo join:          {t_join:.2f} s")
    print(f"Tiempo agregación:    {t_agg:.2f} s")
    print(f"Tiempo escritura:     {t_write:.2f} s")
    print(f"TIEMPO TOTAL:         {total:.2f} s")
    print(f"\nResultado guardado en: {os.path.join(args.out_dir, 'vehicles_curated')} (Parquet, particionado por year)")

    spark.stop()

    return {
        "engine": "spark",
        "original_count": original_count,
        "valid_count": valid_count,
        "rejected_count": rejected_count,
        "written_count": written_count,
        "t_read": t_read, "t_validate": t_val, "t_transform": t_tr,
        "t_join": t_join, "t_aggregate": t_agg, "t_write": t_write,
        "t_total": total,
    }


if __name__ == "__main__":
    main()
