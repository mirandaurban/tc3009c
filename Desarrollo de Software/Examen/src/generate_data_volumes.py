# src/generate_data_volumes.py
"""
Generador de datos para benchmarks de escalabilidad.
Crea volumenes de 60k, 250k, 1M y 4M registros.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_PATH = ROOT_DIR / "config.json"


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_catalogo():
    config = load_config()
    catalogo_path = ROOT_DIR / config["paths"]["catalogo"]
    with catalogo_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_tarifas():
    config = load_config()
    tarifas_path = ROOT_DIR / config["paths"]["tarifas"]
    return pd.read_csv(tarifas_path)


def generate_appointments_df(patient_ids, n_records, seed=42):
    """
    Genera un DataFrame de appointments para un volumen dado
    """
    rng = np.random.default_rng(seed)
    
    catalogo = load_catalogo()
    tarifas = load_tarifas()
    
    clinic_codes = [c["clinic_code"] for c in catalogo["clinicas"]]
    specialties = list(catalogo["especialidad_aliases"].keys())
    
    clinic_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    
    specialty_weights = rng.uniform(0.05, 0.3, len(specialties))
    specialty_weights = specialty_weights / specialty_weights.sum()
    
    weights = rng.lognormal(mean=0.0, sigma=1.1, size=len(patient_ids))
    weights = weights / weights.sum()
    
    tarifa_dict = {}
    for _, row in tarifas.iterrows():
        key = (row["clinic_code"], row["specialty"])
        tarifa_dict[key] = row["tarifa_base"]
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 11, 30)
    days_range = (end_date - start_date).days
    
    data = []
    
    for i in range(n_records):
        appointment_id = f"A{(i + 1):07d}"
        
        patient_idx = int(rng.choice(len(patient_ids), p=weights))
        patient_id = patient_ids[patient_idx]
        
        clinic_code = rng.choice(clinic_codes, p=clinic_weights)
        specialty = rng.choice(specialties, p=specialty_weights)
        
        days_offset = int(rng.integers(0, days_range + 1))
        scheduled_at = start_date + timedelta(days=days_offset)
        
        hour = int(rng.choice(range(8, 19)))
        minute = int(rng.choice([0, 15, 30, 45]))
        scheduled_at = scheduled_at.replace(hour=hour, minute=minute)
        
        duration_min = int(rng.choice([15, 20, 30, 45, 60], p=[0.30, 0.25, 0.25, 0.15, 0.05]))
        
        status = rng.choice(['completada', 'no_show', 'cancelada'], p=[0.78, 0.13, 0.09])
        
        tarifa = tarifa_dict.get((clinic_code, specialty), 1000)
        factor = np.clip(rng.normal(1.0, 0.12), 0.7, 1.6)
        amount_charged = round(float(tarifa * factor), 2)
        
        if status == 'cancelada':
            amount_charged = 0.0
        elif status == 'no_show':
            if rng.random() < 0.85:
                amount_charged = 0.0
            else:
                amount_charged = round(tarifa * 0.30, 2)
        
        payment_method = rng.choice(
            ['efectivo', 'tarjeta', 'transferencia', 'aseguradora'],
            p=[0.30, 0.35, 0.15, 0.20]
        )
        
        days_offset_created = int(rng.integers(1, 46))
        created_at = scheduled_at - timedelta(days=days_offset_created)
        
        tarifa_base = tarifa
        
        data.append({
            'appointment_id': appointment_id,
            'patient_id': patient_id,
            'clinic_code': clinic_code,
            'specialty': specialty,
            'scheduled_at': scheduled_at.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_min': duration_min,
            'status': status,
            'amount_charged': amount_charged,
            'payment_method': payment_method,
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'tarifa_base': tarifa_base,
            'revenue_gap': amount_charged - tarifa_base
        })
    
    return pd.DataFrame(data)


def create_volume_database(df, volume_name):
    """
    Crea una base de datos SQLite con el volumen dado
    """
    volume_dir = DATA_DIR / volume_name
    volume_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = volume_dir / "clinica_curated.db"
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fact_appointments (
                appointment_id TEXT PRIMARY KEY,
                patient_id TEXT,
                clinic_code TEXT,
                specialty TEXT,
                scheduled_at TEXT,
                duration_min INTEGER,
                status TEXT,
                amount_charged REAL,
                payment_method TEXT,
                created_at TEXT,
                tarifa_base REAL,
                revenue_gap REAL
            )
        """)
        
        df_clean = df.copy()
        df_clean['clinic_code_clean'] = df_clean['clinic_code']
        df_clean['specialty_clean'] = df_clean['specialty']
        df_clean['amount_charged_clean'] = df_clean['amount_charged']
        
        df_clean.to_sql('fact_appointments', conn, if_exists='replace', index=False)
    
    print(f"  Volume {volume_name}: {len(df)} registros en {db_path}")
    return db_path


def main():
    print("GENERANDO VOLUMENES DE DATOS PARA BENCHMARK")
    
    config = load_config()
    db_path = ROOT_DIR / config["paths"]["database"]
    
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        print("Ejecuta primero: python3 scripts/seed_database.py")
        sys.exit(1)
    
    with sqlite3.connect(db_path) as conn:
        patients = conn.execute("SELECT patient_id FROM patients").fetchall()
        patient_ids = [p[0] for p in patients]
    
    print(f"\nPacientes disponibles: {len(patient_ids)}")
    
    volumes = [
        ("volume_60k", 60000),
        ("volume_250k", 250000),
        ("volume_1M", 1000000),
        ("volume_4M", 4000000),
    ]
    
    for volume_name, n_records in volumes:
        print(f"\nGenerando {volume_name} ({n_records} registros)...")
        df = generate_appointments_df(patient_ids, n_records, seed=42)
        create_volume_database(df, volume_name)
    
    print("Todos los volúmenes generados")

if __name__ == "__main__":
    main()