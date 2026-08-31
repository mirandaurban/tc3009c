"""
pandas_etl.py — el MISMO pipeline ETL que 07_etl_pipeline.py (Spark),
escrito en pandas puro: READ, VALIDATE, TRANSFORM, JOIN, AGGREGATE, WRITE.

Uso:
    python pandas_etl.py --data-dir data --out-dir output_pandas

Imprime tiempos por etapa y memoria pico aproximada del proceso.
"""
import argparse
import os
import time
import tracemalloc

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="output_pandas")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    tracemalloc.start()
    t0 = time.perf_counter()

    # --- READ ---
    t_read0 = time.perf_counter()
    vehicles = pd.read_csv(os.path.join(args.data_dir, "vehicles.csv"))
    manufacturers = pd.read_csv(os.path.join(args.data_dir, "manufacturers.csv"))
    t_read = time.perf_counter() - t_read0
    original_count = len(vehicles)

    # --- VALIDATE ---
    t_val0 = time.perf_counter()
    is_valid = (
        (vehicles["price"] > 0)
        & (vehicles["year"] >= 1990)
        & (vehicles["year"] <= 2026)
        & (vehicles["mileage"] >= 0)
    )
    valid = vehicles[is_valid]
    rejected = vehicles[~is_valid]
    t_val = time.perf_counter() - t_val0

    # --- TRANSFORM ---
    t_tr0 = time.perf_counter()
    transformed = valid.copy()
    transformed["vehicle_age"] = 2026 - transformed["year"]
    t_tr = time.perf_counter() - t_tr0

    # --- JOIN ---
    t_join0 = time.perf_counter()
    curated = transformed.merge(manufacturers, on="brand", how="left")
    t_join = time.perf_counter() - t_join0

    # --- AGGREGATE ---
    t_agg0 = time.perf_counter()
    summary = (
        curated.groupby("brand")
        .agg(vehicles=("vehicle_id", "count"), avg_price=("price", "mean"))
        .sort_values("avg_price", ascending=False)
    )
    t_agg = time.perf_counter() - t_agg0

    print("\n--- Resumen por marca ---")
    print(summary)

    # --- WRITE (particionado por year, igual que el Parquet de Spark) ---
    t_write0 = time.perf_counter()
    out_path = os.path.join(args.out_dir, "vehicles_curated")
    curated.to_parquet(out_path, partition_cols=["year"], index=False)
    t_write = time.perf_counter() - t_write0

    total = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print("\n--- Reporte del pipeline (pandas) ---")
    print("Registros originales:", original_count)
    print("Registros válidos:   ", len(valid))
    print("Registros rechazados:", len(rejected))
    print("Registros escritos:  ", len(curated))
    print(f"\nTiempo lectura:       {t_read:.2f} s")
    print(f"Tiempo validación:    {t_val:.2f} s")
    print(f"Tiempo transformación:{t_tr:.2f} s")
    print(f"Tiempo join:          {t_join:.2f} s")
    print(f"Tiempo agregación:    {t_agg:.2f} s")
    print(f"Tiempo escritura:     {t_write:.2f} s")
    print(f"TIEMPO TOTAL:         {total:.2f} s")
    print(f"Memoria Python pico (tracemalloc): {peak / (1024 * 1024):.1f} MB")
    print(f"\nResultado guardado en: {out_path} (Parquet, particionado por year)")

    return {
        "engine": "pandas",
        "original_count": original_count,
        "valid_count": len(valid),
        "rejected_count": len(rejected),
        "written_count": len(curated),
        "t_read": t_read, "t_validate": t_val, "t_transform": t_tr,
        "t_join": t_join, "t_aggregate": t_agg, "t_write": t_write,
        "t_total": total, "peak_mb": peak / (1024 * 1024),
    }


if __name__ == "__main__":
    main()
