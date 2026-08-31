"""
run_benchmark.py — corre pandas_etl.py y spark_etl.py como procesos
independientes (para medir memoria real de cada uno por separado),
captura sus tiempos totales y guarda un resumen en benchmark_result.json.

Uso:
    python generate_data.py --rows 50000
    python run_benchmark.py --data-dir data
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time


def run_and_capture(cmd, label):
    print(f"\n{'=' * 60}\nEjecutando: {label}\n{'=' * 60}")
    start_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    end_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print(f"*** {label} terminó con error (código {proc.returncode}) ***")
        print(proc.stderr[-3000:])
    return proc.stdout, wall, proc.returncode, start_iso, end_iso


def extract_total(stdout):
    m = re.search(r"TIEMPO TOTAL:\s*([\d.]+)\s*s", stdout)
    return float(m.group(1)) if m else None


def extract_peak_mb(stdout):
    m = re.search(r"Memoria Python pico.*?:\s*([\d.]+)\s*MB", stdout)
    return float(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-json", default="benchmark_result.json")
    args = ap.parse_args()

    py = sys.executable

    pandas_out, pandas_wall, pandas_rc, pandas_start, pandas_end = run_and_capture(
        [py, "pandas_etl.py", "--data-dir", args.data_dir, "--out-dir", "output_pandas"],
        "pandas_etl.py",
    )
    spark_out, spark_wall, spark_rc, spark_start, spark_end = run_and_capture(
        [py, "spark_etl.py", "--data-dir", args.data_dir, "--out-dir", "output_spark"],
        "spark_etl.py",
    )

    n_rows = None
    vpath = os.path.join(args.data_dir, "vehicles.csv")
    if os.path.exists(vpath):
        with open(vpath) as f:
            n_rows = sum(1 for _ in f) - 1
    size_mb = os.path.getsize(vpath) / (1024 * 1024) if os.path.exists(vpath) else None

    result = {
        "rows": n_rows,
        "csv_size_mb": round(size_mb, 1) if size_mb else None,
        "pandas": {
            "start_time": pandas_start,
            "end_time": pandas_end,
            "wall_time_s": round(pandas_wall, 2),
            "reported_total_s": extract_total(pandas_out),
            "peak_memory_mb": extract_peak_mb(pandas_out),
            "returncode": pandas_rc,
        },
        "spark": {
            "start_time": spark_start,
            "end_time": spark_end,
            "wall_time_s": round(spark_wall, 2),
            "reported_total_s": extract_total(spark_out),
            "returncode": spark_rc,
        },
    }

    with open(args.out_json, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}\nRESUMEN\n{'=' * 60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nGuardado en: {args.out_json}")


if __name__ == "__main__":
    main()
