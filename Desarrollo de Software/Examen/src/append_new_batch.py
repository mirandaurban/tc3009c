"""
Genera un nuevo lote de citas para probar extracción incremental
"""

import json
import sqlite3
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


def get_existing_ids(conn):
    patients = conn.execute("SELECT patient_id FROM patients").fetchall()
    patient_ids = [p[0] for p in patients]
    
    appointments = conn.execute("SELECT appointment_id FROM appointments").fetchall()
    appointment_ids = [a[0] for a in appointments]
    
    return patient_ids, appointment_ids


def generate_new_appointments(patient_ids, existing_appointment_ids, tarifas, catalogo, n_new=2500):
    """
    Generar nuevas citas con fechas recientes
    """
    
    rng = np.random.default_rng(42)
    
    # Extraer datos del catálogo
    clinic_codes = [c["clinic_code"] for c in catalogo["clinicas"]]
    specialties = list(catalogo["especialidad_aliases"].keys())
    
    # Pesos para clínicas
    clinic_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    
    # Pesos para especialidades
    specialty_weights = rng.uniform(0.05, 0.3, len(specialties))
    specialty_weights = specialty_weights / specialty_weights.sum()
    
    # Pesos para pacientes
    weights = rng.lognormal(mean=0.0, sigma=1.1, size=len(patient_ids))
    weights = weights / weights.sum()
    
    # Fechas para las nuevas citas (últimos 15 días)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)
    
    # Crear diccionario de tarifas
    tarifa_dict = {}
    for _, row in tarifas.iterrows():
        key = (row["clinic_code"], row["specialty"])
        tarifa_dict[key] = row["tarifa_base"]
    
    new_appointments = []
    max_id = 0
    
    # Encontrar el máximo appointment_id existente
    for aid in existing_appointment_ids:
        if aid.startswith("A"):
            try:
                num = int(aid[1:])
                if num > max_id:
                    max_id = num
            except:
                pass
    
    for i in range(1, n_new + 1):
        new_id = max_id + i
        appointment_id = f"A{new_id:07d}"
        
        patient_id = rng.choice(patient_ids, p=weights)
        
        clinic_code = rng.choice(clinic_codes, p=clinic_weights)
        specialty = rng.choice(specialties, p=specialty_weights)
        
        days_offset = int(rng.integers(0, 15))
        hours_offset = int(rng.integers(8, 19))
        minutes_offset = int(rng.choice([0, 15, 30, 45]))
        
        # CORREGIDO: Restar días, horas y minutos por separado
        scheduled_at = end_date - timedelta(days=days_offset)
        scheduled_at = scheduled_at - timedelta(hours=hours_offset)
        scheduled_at = scheduled_at - timedelta(minutes=minutes_offset)
        
        duration_min = rng.choice([15, 20, 30, 45, 60], p=[0.30, 0.25, 0.25, 0.15, 0.05])
        
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
        created_at = scheduled_at - timedelta(days=days_offset_created)  # ✅ Esta línea está bien
        
        new_appointments.append({
            'appointment_id': appointment_id,
            'patient_id': patient_id,
            'clinic_code': clinic_code,
            'specialty': specialty,
            'scheduled_at': scheduled_at.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_min': duration_min,
            'status': status,
            'amount_charged': amount_charged,
            'payment_method': payment_method,
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return new_appointments


def append_to_database(conn, new_appointments):
    """
    Añadir las nuevas citas a la base de datos
    """
    
    cursor = conn.cursor()
    
    inserted = 0
    for app in new_appointments:
        try:
            cursor.execute("""
                INSERT INTO appointments (
                    appointment_id, patient_id, clinic_code, specialty,
                    scheduled_at, duration_min, status, amount_charged,
                    payment_method, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app['appointment_id'], app['patient_id'], app['clinic_code'],
                app['specialty'], app['scheduled_at'], app['duration_min'],
                app['status'], app['amount_charged'], app['payment_method'],
                app['created_at']
            ))
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"     Error insertando {app['appointment_id']}: {e}")
    
    conn.commit()
    return inserted


def update_profile(original_count, new_count):
    """
    Actualiza el perfil de datos
    """
    config = load_config()
    profile_path = ROOT_DIR / config["paths"]["profile"]
    
    if profile_path.exists():
        with profile_path.open(encoding="utf-8") as f:
            profile = json.load(f)
        
        profile['n_appointments'] = original_count + new_count
        profile['timestamp'] = datetime.now().isoformat()
        profile['last_append'] = {
            'new_appointments': new_count,
            'timestamp': datetime.now().isoformat()
        }
        
        with profile_path.open('w', encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        
        print(f"    Perfil actualizado: {profile_path}")


def main():
    """
    Función principal
    """
    print("===== APPEND NEW BATCH - Generando nuevas citas ======")
    
    config = load_config()
    db_path = ROOT_DIR / config["paths"]["database"]
    
    if not db_path.exists():
        print(f"    Base de datos no encontrada: {db_path}")
        sys.exit(1)
    
    print(f"   ✓ Base de datos: {db_path}")
    
    catalogo = load_catalogo()
    tarifas = load_tarifas()
    print(f"   ✓ Catálogo: {len(catalogo['clinicas'])} clínicas")
    print(f"   ✓ Tarifas: {len(tarifas)} registros")
    
    conn = sqlite3.connect(db_path)
    
    try:
        patient_ids, appointment_ids = get_existing_ids(conn)
        print(f"   ✓ Pacientes: {len(patient_ids)}")
        print(f"   ✓ Citas existentes: {len(appointment_ids)}")
        
        n_new = 2500
        print(f"\nGenerando {n_new} nuevas citas...")
        new_appointments = generate_new_appointments(
            patient_ids, appointment_ids, tarifas, catalogo, n_new
        )
        print(f"   ✓ {len(new_appointments)} citas generadas")
        
        inserted = append_to_database(conn, new_appointments)
        print(f"   ✓ {inserted} citas insertadas")
        
        print("\nActualizando perfil...")
        update_profile(len(appointment_ids), inserted)
        
        print("\n====== BATCH COMPLETADO ======")
        print(f"   Nuevas citas: {inserted}")
        print(f"   Total citas: {len(appointment_ids) + inserted}")
        print(f"\n   Ahora ejecuta: python3 src/etl.py")
        print("   para procesar las nuevas citas incrementalmente")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()