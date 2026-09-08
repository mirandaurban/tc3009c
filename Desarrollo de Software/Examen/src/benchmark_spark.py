# src/benchmark_spark.py
"""
Benchmark de escalabilidad: Pandas vs PySpark
Lee datos desde archivos CSV generados previamente.
"""

import time
import json
import sqlite3
import sys
from pathlib import Path
import pandas as pd
import numpy as np

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, sum as spark_sum, avg, count, date_format, when
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False
    print("PySpark no disponible. Instala: pip install pyspark")

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"


def export_db_to_csv(db_path: Path, csv_path: Path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM fact_appointments", conn)
    conn.close()
    df.to_csv(csv_path, index=False)
    print(f"  Exportado a CSV: {csv_path} ({len(df)} filas)")
    return csv_path


class Benchmark:
    def __init__(self):
        self.results = {"pandas": {}, "spark": {}}
        self.spark = None
        
        if SPARK_AVAILABLE:
            self.spark = SparkSession.builder \
                .appName("ETL_Benchmark") \
                .config("spark.master", "local[*]") \
                .config("spark.sql.shuffle.partitions", "8") \
                .config("spark.driver.memory", "4g") \
                .getOrCreate()
    
    def stop_spark(self):
        if self.spark:
            self.spark.stop()
    
    def read_csv_pandas(self, csv_path):
        return pd.read_csv(csv_path)
    
    def read_csv_spark(self, csv_path):
        return self.spark.read.csv(str(csv_path), header=True, inferSchema=True)
    
    def aggregate_pandas(self, df):
        df_clean = df.copy()
        df_clean['scheduled_date'] = pd.to_datetime(df_clean['scheduled_at'])
        df_clean['mes'] = df_clean['scheduled_date'].dt.strftime('%Y-%m')
        df_clean['is_no_show'] = (df_clean['status'] == 'no_show').astype(int)
        
        result = df_clean.groupby(['clinic_code', 'specialty', 'mes']).agg(
            total_citas=('appointment_id', 'count'),
            ingreso_total=('amount_charged', 'sum'),
            ticket_promedio=('amount_charged', 'mean'),
            no_show_count=('is_no_show', 'sum')
        ).reset_index()
        
        result['tasa_no_show'] = result['no_show_count'] / result['total_citas']
        return result
    
    def aggregate_spark(self, df):
        df_clean = df.withColumn("mes", date_format(col("scheduled_at"), "yyyy-MM")) \
                     .withColumn("is_no_show", when(col("status") == "no_show", 1).otherwise(0))
        
        result = df_clean.groupBy("clinic_code", "specialty", "mes").agg(
            count("appointment_id").alias("total_citas"),
            spark_sum("amount_charged").alias("ingreso_total"),
            avg("amount_charged").alias("ticket_promedio"),
            spark_sum("is_no_show").alias("no_show_count")
        )
        
        result = result.withColumn("tasa_no_show", col("no_show_count") / col("total_citas"))
        return result
    
    def run_benchmark(self, volume_name, csv_path, repetitions=3):
        print(f"\n  {volume_name}...")
        
        pandas_times = []
        for rep in range(repetitions):
            start = time.perf_counter()
            df = self.read_csv_pandas(csv_path)
            result = self.aggregate_pandas(df)
            elapsed = time.perf_counter() - start
            pandas_times.append(elapsed)
            print(f"    Pandas rep {rep+1}: {elapsed:.2f}s")
        
        pandas_median = np.median(pandas_times)
        print(f"    Pandas mediana: {pandas_median:.2f}s")
        self.results["pandas"][volume_name] = pandas_median
        
        if SPARK_AVAILABLE:
            spark_times = []
            for rep in range(repetitions):
                start = time.perf_counter()
                df = self.read_csv_spark(csv_path)
                result = self.aggregate_spark(df)
                result.collect()
                elapsed = time.perf_counter() - start
                spark_times.append(elapsed)
                print(f"    Spark rep {rep+1}: {elapsed:.2f}s")
            
            spark_median = np.median(spark_times)
            print(f"    Spark mediana: {spark_median:.2f}s")
            self.results["spark"][volume_name] = spark_median
    
    def measure_spark_overhead(self, repetitions=5):
        if not SPARK_AVAILABLE:
            return None
        
        print("\nMidiendo overhead de Spark...")
        overhead_times = []
        
        for rep in range(repetitions):
            start = time.perf_counter()
            spark = SparkSession.builder \
                .appName("Overhead_Test") \
                .config("spark.master", "local[*]") \
                .getOrCreate()
            spark.range(10).collect()
            spark.stop()
            elapsed = time.perf_counter() - start
            overhead_times.append(elapsed)
            print(f"  Rep {rep+1}: {elapsed:.2f}s")
        
        overhead_median = np.median(overhead_times)
        print(f"  Overhead mediano: {overhead_median:.2f}s")
        return overhead_median
    
    def show_exchange_plan(self, csv_path):
        if not SPARK_AVAILABLE:
            return None
        
        print("\nPlan de ejecucion de Spark (Exchange):")
        
        df = self.read_csv_spark(csv_path)
        result = self.aggregate_spark(df)
        
        print("  Physical Plan:")
        print(result._jdf.queryExecution().executedPlan().toString())
        
        return result._jdf.queryExecution().executedPlan().toString()
    
    def analyze_skew(self, csv_path):
        if not SPARK_AVAILABLE:
            return None
        
        print("\nAnalizando skew de pacientes...")
        
        df = self.read_csv_spark(csv_path)
        
        patient_counts = df.groupBy("patient_id").count().orderBy(col("count").desc())
        counts = patient_counts.select("count").rdd.flatMap(lambda x: x).collect()
        
        if not counts:
            return None
        
        total_patients = len(counts)
        total_citas = sum(counts)
        
        sorted_counts = sorted(counts, reverse=True)
        top_30_count = sum(sorted_counts[:int(total_patients * 0.3)])
        skew_ratio = top_30_count / total_citas if total_citas > 0 else 0
        
        print(f"  Top 30% pacientes: {skew_ratio*100:.1f}% de las citas")
        print(f"  Total pacientes: {total_patients}")
        print(f"  Total citas: {total_citas}")
        print(f"  Max citas por paciente: {max(counts)}")
        print(f"  Min citas por paciente: {min(counts)}")
        print(f"  Promedio citas por paciente: {total_citas/total_patients:.1f}")
        
        return {
            "skew_ratio": skew_ratio,
            "total_patients": total_patients,
            "total_citas": total_citas,
            "max_citas": max(counts),
            "min_citas": min(counts),
            "avg_citas": total_citas/total_patients
        }
    
    def run_full_benchmark(self):
        print("=" * 60)
        print("BENCHMARK PANDAS VS PYSPARK")
        print("=" * 60)
        
        # Exportar cada volumen a CSV
        volumes = [
            ("60K", DATA_DIR / "volume_60k" / "clinica_curated.db", 
                    DATA_DIR / "volume_60k" / "fact_appointments.csv"),
            ("250K", DATA_DIR / "volume_250k" / "clinica_curated.db", 
                     DATA_DIR / "volume_250k" / "fact_appointments.csv"),
            ("1M", DATA_DIR / "volume_1M" / "clinica_curated.db", 
                   DATA_DIR / "volume_1M" / "fact_appointments.csv"),
            ("4M", DATA_DIR / "volume_4M" / "clinica_curated.db", 
                   DATA_DIR / "volume_4M" / "fact_appointments.csv"),
        ]
        
        for label, db_path, csv_path in volumes:
            if not db_path.exists():
                print(f"\n  {label}: archivo DB no encontrado")
                continue
            
            # Exportar a CSV si no existe
            if not csv_path.exists():
                export_db_to_csv(db_path, csv_path)
            
            self.run_benchmark(label, csv_path)
        
        # Mostrar plan de Exchange con el primer volumen disponible
        for label, db_path, csv_path in volumes:
            if csv_path.exists():
                self.show_exchange_plan(csv_path)
                self.analyze_skew(csv_path)
                break
        
        overhead = self.measure_spark_overhead()
        self.results["spark_overhead"] = overhead
        
        self.save_results()
        self.plot_results()
        
        return self.results
    
    def save_results(self):
        output_path = DATA_DIR / "benchmark_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResultados guardados en: {output_path}")
    
    def plot_results(self):
        try:
            import matplotlib.pyplot as plt
            
            pandas_data = self.results.get("pandas", {})
            spark_data = self.results.get("spark", {})
            
            volumes = ["60K", "250K", "1M", "4M"]
            pandas_times = [pandas_data.get(v, 0) for v in volumes]
            spark_times = [spark_data.get(v, 0) for v in volumes]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = np.arange(len(volumes))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, pandas_times, width, label='Pandas', color='#1f77b4')
            bars2 = ax.bar(x + width/2, spark_times, width, label='PySpark', color='#ff7f0e')
            
            ax.set_xlabel('Volumen de datos')
            ax.set_ylabel('Tiempo de ejecucion (segundos)')
            ax.set_title('Benchmark: Pandas vs PySpark')
            ax.set_xticks(x)
            ax.set_xticklabels(volumes)
            ax.legend()
            
            for bar, value in zip(bars1, pandas_times):
                if value > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                           f'{value:.1f}s', ha='center', va='bottom', fontsize=9)
            
            for bar, value in zip(bars2, spark_times):
                if value > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                           f'{value:.1f}s', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            output_path = DATA_DIR / "benchmark_results.png"
            plt.savefig(output_path, dpi=150)
            print(f"Grafica guardada en: {output_path}")
            
        except ImportError:
            print("matplotlib no disponible. Instala: pip install matplotlib")


def main():
    benchmark = Benchmark()
    results = benchmark.run_full_benchmark()
    
    print("RESUMEN DE RESULTADOS:")
    
    print("\nTiempos de ejecucion (mediana, segundos):")
    print("  Volumen | Pandas | PySpark | Ratio")
    print("  " + "-" * 45)
    
    for vol in ["60K", "250K", "1M", "4M"]:
        p_time = results.get("pandas", {}).get(vol, 0)
        s_time = results.get("spark", {}).get(vol, 0)
        if p_time > 0 and s_time > 0:
            ratio = p_time / s_time if s_time > 0 else 0
            print(f"  {vol:>7} | {p_time:>6.1f}s | {s_time:>6.1f}s | {ratio:>5.1f}x")
        elif p_time > 0:
            print(f"  {vol:>7} | {p_time:>6.1f}s | {'N/A':>6} | {'N/A':>5}")
    
    if results.get("spark_overhead"):
        print(f"\nOverhead de arranque de Spark: {results['spark_overhead']:.2f}s")
    
    benchmark.stop_spark()


if __name__ == "__main__":
    main()