"""
Verificación del pipeline ETL
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_PATH = ROOT_DIR / "config.json"


def load_config():
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_db_connection():
    config = load_config()
    db_path = ROOT_DIR / config["paths"]["output_database"]
    
    if not db_path.exists():
        print(f"Base de datos no encontrada: {db_path}")
        return None
    
    return sqlite3.connect(db_path)


def verify_counts(conn):
    print("\n• Conteos de registros")
    
    tables = {
        "fact_appointments": "Citas curadas",
        "quarantine": "Registros en cuarentena",
        "etl_runs": "Ejecuciones ETL"
    }
    
    total = 0
    for table, description in tables.items():
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {description}: {count:,}")
            total += count
        except sqlite3.OperationalError:
            print(f"   {description}:Tabla no existe")
    
    return total


def verify_reject_reasons(conn):
    print("\n• Motivos de rechazo (appointments)")
    
    try:
        cursor = conn.execute("""
            SELECT reject_reason FROM quarantine 
            WHERE source = 'appointments'
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("   No hay registros en cuarentena")
            return
        
        from collections import Counter
        all_reasons = Counter()
        
        for row in rows:
            reasons = row[0].split(';')
            for reason in reasons:
                if reason:  # Evitar strings vacíos
                    all_reasons[reason] += 1
        
        total_rejected = sum(all_reasons.values())
        
        for reason, count in all_reasons.most_common():
            percentage = (count / total_rejected) * 100
            print(f"    {reason}: {count} ({percentage:.1f}%)")
        
        print(f"\n   Total rechazos: {total_rejected}")
        
    except sqlite3.OperationalError:
        print("    Tabla quarantine no existe o no tiene datos")


def verify_last_run(conn):
    print("\n• Última ejecución ETL")
    
    try:
        cursor = conn.execute("""
            SELECT run_id, started_at, finished_at, 
                   source_appointments, valid_appointments, 
                   quarantined_appointments, inserted, updated,
                   quality_status, status
            FROM etl_runs 
            ORDER BY started_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if not row:
            print("   No hay ejecuciones registradas")
            return
        
        (run_id, started_at, finished_at, 
         source, valid, quarantined, inserted, updated,
         quality_status, status) = row
        
        print(f"   Run ID: {run_id}")
        print(f"   Inicio: {started_at}")
        print(f"   Fin: {finished_at}")
        print(f"   Estado: {status}")
        print(f"   Quality Gate: {quality_status}")
        print(f"\n   Citas fuente: {source:,}")
        print(f"   Citas válidas: {valid:,}")
        print(f"   Citas en cuarentena: {quarantined:,}")
        print(f"   Insertadas: {inserted:,}")
        print(f"   Actualizadas: {updated:,}")
        
        # Calcular tasa de rechazo
        if source > 0:
            reject_rate = (quarantined / source) * 100
            print(f"   Tasa de rechazo: {reject_rate:.1f}%")
        
    except sqlite3.OperationalError:
        print("     Tabla etl_runs no existe")


def verify_idempotency(conn):
    print("\n• Verificación de idempotencia")
    
    try:
        cursor = conn.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(DISTINCT appointment_id) as unique_count
            FROM fact_appointments
        """)
        total, unique = cursor.fetchone()
        
        if total == unique:
            print(f"    Sin duplicados: {total} registros únicos")
        else:
            duplicates = total - unique
            print(f"     {duplicates} duplicados encontrados")
            print(f"      Total: {total}, Únicos: {unique}")
            
            cursor = conn.execute("""
                SELECT appointment_id, COUNT(*) as cnt 
                FROM fact_appointments 
                GROUP BY appointment_id 
                HAVING cnt > 1
                LIMIT 5
            """)
            dup_rows = cursor.fetchall()
            if dup_rows:
                print("   Ejemplos de duplicados:")
                for row in dup_rows:
                    print(f"      - {row[0]}: {row[1]} veces")
                    
    except sqlite3.OperationalError:
        print("     Tabla fact_appointments no existe")


def main():
    print("====== VERIFICACIÓN ETL =====")
    print(f"Fecha de verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    
    try:
        verify_counts(conn)
        verify_reject_reasons(conn)
        verify_last_run(conn)
        verify_idempotency(conn)
        
        print("\nVERIFICACIÓN COMPLETADA")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()