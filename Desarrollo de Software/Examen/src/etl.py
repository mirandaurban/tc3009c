"""
ETL Pipeline para el sistema de citas médicas

Pipeline: DEFINE → EXTRACT → STAGE → VALIDATE → TRANSFORM → INTEGRATE → QUALITY GATE → LOAD → AUDIT
"""

import json
import sqlite3
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional, Set
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

# Importar contratos
from contracts import (
    ALL_CONTRACTS,
    VALID_SPECIALTIES,
    VALID_CLINIC_CODES,
    VALID_CITIES,
    VALID_INSURANCE,
    VALID_STATUSES,
    VALID_PAYMENT_METHODS,
    VALID_DURATIONS,
    VALID_CURRENCIES,
    PATIENTS_CONTRACT,
    APPOINTMENTS_CONTRACT,
    TARIFAS_CONTRACT,
    FACT_APPOINTMENTS_CONTRACT,
    QUARANTINE_CONTRACT,
    AUDIT_CONTRACT
)

# Directorios del proyecto
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent  
CONFIG_PATH = PROJECT_ROOT / "config.json"
DATA_DIR = PROJECT_ROOT / "data"
WATERMARK_DIR = PROJECT_ROOT / "data"

# Configuración de logging
def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


"""
DEFINE: Contrato de configuración del pipeline
"""
@dataclass(frozen=True)
class ETLConfig:
    database_path: Path
    tarifas_path: Path
    catalogo_path: Path
    profile_path: Path
    watermark_path: Path
    output_database_path: Path
    log_file_path: Path
    fact_appointments_table: str
    quarantine_table: str
    audit_table: str
    completeness_min: float
    duplicate_rate_max: float
    null_foreign_key_max: float
    invalid_amount_max: float
    max_rule_violation_pct: float
    allowed_statuses: List[str]
    allowed_payment_methods: List[str]
    watermark_column: str = "created_at"


def load_config(config_path: Path = None) -> ETLConfig:
    """Cargar configuración desde archivo JSON"""
    with config_path.open(encoding="utf-8") as file:
        raw = json.load(file)
    
    paths = raw["paths"]
    output_tables = raw["output_tables"]
    quality = raw["quality_thresholds"]
    watermark_filename = Path(paths["watermark"]).name
    
    return ETLConfig(       
        database_path=PROJECT_ROOT / paths["database"],
        tarifas_path=PROJECT_ROOT / paths["tarifas"],
        catalogo_path=PROJECT_ROOT / paths["catalogo"],
        profile_path=PROJECT_ROOT / paths["profile"],
        watermark_path=WATERMARK_DIR / watermark_filename,
        output_database_path=PROJECT_ROOT / paths["output_database"],
        log_file_path=PROJECT_ROOT / paths["log_file"],
        fact_appointments_table=output_tables["fact_appointments"],
        quarantine_table=output_tables["quarantine"],
        audit_table=output_tables["audit"],
        completeness_min=quality["completeness_min"],
        duplicate_rate_max=quality["duplicate_rate_max"],
        null_foreign_key_max=quality["null_foreign_key_max"],
        invalid_amount_max=quality["invalid_amount_max"],
        max_rule_violation_pct=quality["max_rule_violation_pct"],
        allowed_statuses=raw["allowed_statuses"],
        allowed_payment_methods=raw["allowed_payment_methods"],
    )


def read_watermark(path: Path) -> str:
    """Leer el último watermark procesado"""
    if not path.exists():
        return "2024-01-01 00:00:00" # De acurdo al primer appointment
    
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
        return data.get("last_processed_at", "2024-01-01 00:00:00")


def write_watermark(path: Path, value: str) -> None:
    """Escribir el nuevo watermark después del procesamiento"""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    current_data = {}
    if path.exists():
        with path.open(encoding="utf-8") as file:
            current_data = json.load(file)
    
    current_data["last_processed_at"] = value
    current_data["updated_at"] = datetime.now().isoformat()
    
    path.write_text(
        json.dumps(current_data, indent=2),
        encoding="utf-8"
    )
"""
EXTRACT: Extracción incremental de cada fuente
"""
def extract(config: ETLConfig, watermark: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    # 1. PATIENTS TABLE
    with sqlite3.connect(config.database_path) as conn:
        patients_df = pd.read_sql(
            "SELECT * FROM patients",
            conn
        )
    
    # 2. APPOINTMENTS
    with sqlite3.connect(config.database_path) as conn:
        appointments_df = pd.read_sql(
            """
            SELECT * FROM appointments 
            WHERE created_at > :watermark
            """,
            conn,
            params={"watermark": watermark}
        )
    
    # 3. TARIFAS
    tarifas_df = pd.read_csv(config.tarifas_path)
    
    # 4. CLINICAS
    with config.catalogo_path.open(encoding="utf-8") as file:
        catalogo_clinicas = json.load(file)
    
    # Log de resumen
    logging.info(
        "EXTRACT: %s citas nuevas/modificadas desde watermark=%s | "
        "%s pacientes | %s tarifas | %s clínicas",
        len(appointments_df),
        watermark,
        len(patients_df),
        len(tarifas_df),
        len(catalogo_clinicas)
    )
    
    return patients_df, appointments_df, tarifas_df, catalogo_clinicas

"""
STAGE: Con fines de trazabilidad, añadir evidencia de origen e identificadores
"""
def stage(
    patients_df: pd.DataFrame, 
    appointments_df: pd.DataFrame, 
    tarifas_df: pd.DataFrame,
    batch_id: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ingested_at = pd.Timestamp.now("UTC").isoformat()
    
    # Pacientes
    patients_df = patients_df.copy()
    patients_df["source_system"] = "sqlite:patients"
    patients_df["batch_id"] = batch_id
    patients_df["ingested_at"] = ingested_at
    
    # Citas
    appointments_df = appointments_df.copy()
    appointments_df["source_system"] = "sqlite:appointments"
    appointments_df["batch_id"] = batch_id
    appointments_df["ingested_at"] = ingested_at
    
    # Tarifas
    tarifas_df = tarifas_df.copy()
    tarifas_df["source_system"] = "csv:tarifas_especialidad"
    tarifas_df["batch_id"] = batch_id
    tarifas_df["ingested_at"] = ingested_at
    
    logging.info(
        "STAGE: batch_id=%s asignado a %s pacientes, %s citas, %s tarifas",
        batch_id,
        len(patients_df),
        len(appointments_df),
        len(tarifas_df)
    )
    
    return patients_df, appointments_df, tarifas_df

"""
VALIDATE: Verificar que los datos cumplan con el contrato de datos.
Aquí se define si siguen el proceso o van a cuarentena.
"""
def validate(
    patients_df: pd.DataFrame,
    appointments_df: pd.DataFrame,
    tarifas_df: pd.DataFrame,
    config: ETLConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    # Patients
    p = patients_df.copy()
    p_reasons = [] # Justificaciones de rechazo
    for idx, row in p.iterrows():
        reasons = []
        
        # Contract: patient_id
        if not pd.isna(row.get("patient_id")):
            import re
            if not re.match(r"^P\d{6}$", str(row["patient_id"])):
                reasons.append("patient_id_invalid_format")
        else:
            reasons.append("patient_id_null")
        
        # Contract: birth_date en formato y rango
        if not pd.isna(row.get("birth_date")):
            try:
                birth = pd.to_datetime(row["birth_date"])
                if birth.year < 1940 or birth.year > 2015:
                    reasons.append("birth_date_out_of_range")
            except:
                reasons.append("birth_date_invalid_format")
        else:
            reasons.append("birth_date_null")
        
        # Contract: sex con valores pre-establecidos
        if not pd.isna(row.get("sex")):
            if row["sex"] not in ["F", "M"]:
                reasons.append("sex_invalid")
        else:
            reasons.append("sex_null")
        
        # Contract: city con valores pre-establecidos
        if not pd.isna(row.get("city")):
            if row["city"] not in VALID_CITIES:
                reasons.append("city_invalid")
        else:
            reasons.append("city_null")
        
        # Contract: insurance con valores pre-establecidos
        if not pd.isna(row.get("insurance")):
            if row["insurance"] not in VALID_INSURANCE:
                reasons.append("insurance_invalid")
        else:
            reasons.append("insurance_null")
        
        # Contract: registered_at con formato y rango
        if not pd.isna(row.get("registered_at")):
            try:
                reg = pd.to_datetime(row["registered_at"])
                if reg.year < 2022 or reg.year > 2024:
                    reasons.append("registered_at_out_of_range")
            except:
                reasons.append("registered_at_invalid_format")
        else:
            reasons.append("registered_at_null")
        
        p_reasons.append(";".join(reasons))
    
    p["rejection_reason"] = p_reasons
    quarantined_patients = p[p["rejection_reason"] != ""].copy()
    valid_patients = p[p["rejection_reason"] == ""].copy()

    
    # Appointments
    a = appointments_df.copy()
    a_reasons = [] # Justificaciones de rechazo
    for idx, row in a.iterrows():
        reasons = []
        
        # Contract: appointment_id
        if not pd.isna(row.get("appointment_id")):
            import re
            if not re.match(r"^A\d{7}$", str(row["appointment_id"])):
                reasons.append("appointment_id_invalid_format")
        else:
            reasons.append("appointment_id_null")
        
        # Contract: patient_id con FK válida
        if pd.isna(row.get("patient_id")):
            reasons.append("patient_id_null")
        else:
            # patient_id existe en valid_patients
            if len(valid_patients) > 0 and row["patient_id"] not in valid_patients["patient_id"].values:
                reasons.append("patient_id_fk_missing")
        
        # Contract: clinic_code con valores pre-definidos
        if not pd.isna(row.get("clinic_code")):
            if row["clinic_code"] not in VALID_CLINIC_CODES:
                reasons.append("clinic_code_invalid")
        else:
            reasons.append("clinic_code_null")
        
        # Contract: specialty con valores pre-definidos
            if row["specialty"] not in VALID_SPECIALTIES:
                reasons.append("specialty_invalid")
        
        # Contract: scheduled_at con formato y rangos válidos
        if not pd.isna(row.get("scheduled_at")):
            try:
                pd.to_datetime(row["scheduled_at"])
            except:
                reasons.append("scheduled_at_invalid_format")
        else:
            reasons.append("scheduled_at_null")
        
        # Contract: duration_min con valores pre-definidos
        if not pd.isna(row.get("duration_min")):
            if row["duration_min"] not in VALID_DURATIONS:
                reasons.append("duration_min_invalid")
        else:
            reasons.append("duration_min_null")
        
        # Contract: status con valores pre-definidos
        if not pd.isna(row.get("status")):
            if row["status"] not in VALID_STATUSES:
                reasons.append("status_invalid")
        else:
            reasons.append("status_null")
        
        # Contract: amount_charged con valores pre-definidos
        if not pd.isna(row.get("amount_charged")):
            if row["amount_charged"] < 0:
                reasons.append("amount_charged_negative")
        
        # Contract: payment_method con valores pre-definidos
        if not pd.isna(row.get("payment_method")):
            if row["payment_method"] not in VALID_PAYMENT_METHODS:
                reasons.append("payment_method_invalid")
        else:
            reasons.append("payment_method_null")
        
        # Contract: created_at con formato y rangos válidos
        if not pd.isna(row.get("created_at")):
            try:
                pd.to_datetime(row["created_at"])
            except:
                reasons.append("created_at_invalid_format")
        else:
            reasons.append("created_at_null")
        
        # Regla de negocio: scheduled_at debe ser >= created_at
        if not pd.isna(row.get("scheduled_at")) and not pd.isna(row.get("created_at")):
            try:
                scheduled = pd.to_datetime(row["scheduled_at"])
                created = pd.to_datetime(row["created_at"])
                if scheduled < created:
                    reasons.append("scheduled_before_created")
            except:
                pass 
        
        a_reasons.append(";".join(reasons))
    
    a["rejection_reason"] = a_reasons
    quarantined_appointments = a[a["rejection_reason"] != ""].copy()
    valid_appointments = a[a["rejection_reason"] == ""].copy()

    
    # Tarifas
    t = tarifas_df.copy()
    t_reasons = []
    
    for idx, row in t.iterrows():
        reasons = []
        
        # Contract: clinic_code con valores pre-definidos
        if not pd.isna(row.get("clinic_code")):
            if row["clinic_code"] not in VALID_CLINIC_CODES:
                reasons.append("clinic_code_invalid")
        else:
            reasons.append("clinic_code_null")
        
        # Contract: specialty con valores pre-definidos
        if not pd.isna(row.get("specialty")):
            if row["specialty"] not in VALID_SPECIALTIES:
                reasons.append("specialty_invalid")
        
        # Contract: tarifa_base con rango definido
        if not pd.isna(row.get("tarifa_base")):
            if row["tarifa_base"] < 450 or row["tarifa_base"] > 2200:
                reasons.append("tarifa_base_out_of_range")
            # Verificar que sea múltiplo de 50
            if row["tarifa_base"] % 50 != 0:
                reasons.append("tarifa_base_not_multiple_50")
        else:
            reasons.append("tarifa_base_null")
        
        # Contract: moneda con valores pre-definidos
        if not pd.isna(row.get("moneda")):
            if row["moneda"] not in VALID_CURRENCIES:
                reasons.append("moneda_invalid")
        else:
            reasons.append("moneda_null")
        
        # Contract: vigencia_desde con formato correcto
        if not pd.isna(row.get("vigencia_desde")):
            try:
                pd.to_datetime(row["vigencia_desde"])
            except:
                reasons.append("vigencia_desde_invalid_format")
        else:
            reasons.append("vigencia_desde_null")
        
        t_reasons.append(";".join(reasons))
    
    t["rejection_reason"] = t_reasons
    quarantined_tarifas = t[t["rejection_reason"] != ""].copy()
    valid_tarifas = t[t["rejection_reason"] == ""].copy()
    
    # Cuarentena
    quarantine_records = []
    
    # Pacientes en cuarentena
    for _, row in quarantined_patients.iterrows():
        quarantine_records.append({
            "source": "patients",
            "batch_id": row.get("batch_id", ""),
            "record_id": row.get("patient_id", ""),
            "reject_reason": row.get("rejection_reason", ""),
            "ingested_at": row.get("ingested_at", datetime.now().isoformat())
        })
    
    # Citas en cuarentena
    for _, row in quarantined_appointments.iterrows():
        quarantine_records.append({
            "source": "appointments",
            "batch_id": row.get("batch_id", ""),
            "record_id": row.get("appointment_id", ""),
            "reject_reason": row.get("rejection_reason", ""),
            "ingested_at": row.get("ingested_at", datetime.now().isoformat())
        })
    
    # Tarifas en cuarentena
    for _, row in quarantined_tarifas.iterrows():
        quarantine_records.append({
            "source": "tarifas",
            "batch_id": row.get("batch_id", ""),
            "record_id": f"{row.get('clinic_code', '')}_{row.get('specialty', '')}",
            "reject_reason": row.get("rejection_reason", ""),
            "ingested_at": row.get("ingested_at", datetime.now().isoformat())
        })
    
    quarantine_df = pd.DataFrame(quarantine_records)
    
    logging.info(
        "VALIDATE TOTAL: validos=%s quarantine=%s",
        len(valid_patients) + len(valid_appointments) + len(valid_tarifas),
        len(quarantine_records)
    )
    
    return valid_patients, valid_appointments, valid_tarifas, quarantine_df

"""
TRANSFORM: Homologación y estandarización de variables para uniformidad y determinismo
"""
def transform(
    valid_patients: pd.DataFrame,
    valid_appointments: pd.DataFrame,
    valid_tarifas: pd.DataFrame,
    config: ETLConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    # Patients
    patients = valid_patients.copy()
    
    patients["city"] = patients["city"].str.strip().str.title()
    patients["insurance"] = patients["insurance"].str.strip().str.lower()
    patients["sex"] = patients["sex"].str.strip().str.upper()
    
    patients["birth_date"] = pd.to_datetime(patients["birth_date"])
    patients["registered_at"] = pd.to_datetime(patients["registered_at"])
    
    logging.info(
        "TRANSFORM pacientes (alt): %s transformados",
        len(patients)
    )
    
    # Appointments
    appointments = valid_appointments.copy()
    
    appointments["clinic_code"] = appointments["clinic_code"].str.strip().str.upper()
    appointments["status"] = appointments["status"].str.strip().str.lower()
    appointments["payment_method"] = appointments["payment_method"].str.strip().str.lower()
    
    if "specialty" in appointments.columns:
        appointments["specialty_clean"] = appointments["specialty"].str.strip().str.title()
        appointments["specialty_clean"] = appointments["specialty_clean"].where(
            appointments["specialty"].notna(), None
        )
    else:
        appointments["specialty_clean"] = None
    
    appointments["clinic_code_clean"] = appointments["clinic_code"]
    
    if "amount_charged" in appointments.columns:
        appointments["amount_charged_clean"] = appointments["amount_charged"].fillna(0)
        appointments["amount_charged_clean"] = appointments["amount_charged_clean"].clip(lower=0)
    else:
        appointments["amount_charged_clean"] = 0
    
    appointments["scheduled_at"] = pd.to_datetime(appointments["scheduled_at"])
    appointments["created_at"] = pd.to_datetime(appointments["created_at"])
    
    appointments["scheduled_date"] = appointments["scheduled_at"].dt.date
    appointments["scheduled_hour"] = appointments["scheduled_at"].dt.hour
    appointments["scheduled_day_of_week"] = appointments["scheduled_at"].dt.dayofweek
    appointments["scheduled_month"] = appointments["scheduled_at"].dt.month
    
    appointments["is_peak_hour"] = ((appointments["scheduled_hour"] >= 9) & 
                                     (appointments["scheduled_hour"] <= 13)).astype(int)
    
    appointments["duration_hours"] = appointments["duration_min"] / 60.0
    
    appointments["is_no_show"] = (appointments["status"] == "no_show").astype(int)
    
    appointments["patient_age_at_visit"] = None
    
    logging.info(
        "TRANSFORM citas (alt): %s transformadas",
        len(appointments)
    )
    
    # Tarifas
    tarifas = valid_tarifas.copy()
    
    tarifas["clinic_code"] = tarifas["clinic_code"].str.strip().str.upper()
    tarifas["specialty"] = tarifas["specialty"].str.strip().str.title()
    tarifas["moneda"] = tarifas["moneda"].str.strip().str.upper()
    tarifas["vigencia_desde"] = pd.to_datetime(tarifas["vigencia_desde"])
    
    logging.info(
        "TRANSFORM tarifas (alt): %s transformadas",
        len(tarifas)
    )
    
    return patients, appointments, tarifas

"""
INTEGRATE: Combinación de todas las fuentes respetando cardinalidad
"""
def integrate(
    patients: pd.DataFrame,
    appointments: pd.DataFrame,
    tarifas: pd.DataFrame,
    config: ETLConfig,
) -> tuple[pd.DataFrame, dict]:
    rows_before = len(appointments)
    
    # JOIN: appointments + patients
    patient_dict = {}
    for _, row in patients.iterrows():
        patient_id = row["patient_id"]
        patient_dict[patient_id] = {
            "birth_date": row["birth_date"],
            "sex": row["sex"],
            "city": row["city"],
            "insurance": row["insurance"],
            "registered_at": row["registered_at"]
        }
    
    fact = appointments.copy()
    
    fact["scheduled_at"] = pd.to_datetime(fact["scheduled_at"])
    
    def get_patient_value(pid, key):
        if pid in patient_dict:
            return patient_dict[pid].get(key)
        return None
    
    fact["patient_birth_date"] = fact["patient_id"].apply(lambda pid: get_patient_value(pid, "birth_date"))
    fact["patient_sex"] = fact["patient_id"].apply(lambda pid: get_patient_value(pid, "sex"))
    fact["patient_city"] = fact["patient_id"].apply(lambda pid: get_patient_value(pid, "city"))
    fact["patient_insurance"] = fact["patient_id"].apply(lambda pid: get_patient_value(pid, "insurance"))
    fact["patient_registered_at"] = fact["patient_id"].apply(lambda pid: get_patient_value(pid, "registered_at"))
    
    fact["patient_age_at_visit"] = None
    
    fact["patient_birth_date"] = pd.to_datetime(fact["patient_birth_date"], errors='coerce')
    
    mask = fact["patient_birth_date"].notna() & fact["scheduled_at"].notna()
    
    if mask.any():
        fact.loc[mask, "patient_age_at_visit"] = (
            fact.loc[mask, "scheduled_at"].dt.year - 
            fact.loc[mask, "patient_birth_date"].dt.year
        )

        mask_adjust = mask & (fact["scheduled_at"].dt.month < fact["patient_birth_date"].dt.month)
        fact.loc[mask_adjust, "patient_age_at_visit"] = fact.loc[mask_adjust, "patient_age_at_visit"] - 1
    
    # JOIN: fact + tarifas (por clinic_code + specialty)
    tarifa_dict = {}
    for _, row in tarifas.iterrows():
        key = (row["clinic_code"], row["specialty"])
        tarifa_dict[key] = row["tarifa_base"]
    
    fact["tarifa_base"] = fact.apply(
        lambda row: tarifa_dict.get((row["clinic_code_clean"], row["specialty_clean"])),
        axis=1
    )
    
    # revenue_gap = amount_charged - tarifa_base
    fact["revenue_gap"] = fact["amount_charged_clean"] - fact["tarifa_base"]
    
    # Añadir metadatos del stage
    if "batch_id" not in fact.columns:
        fact["batch_id"] = "unknown"
    if "source_system" not in fact.columns:
        fact["source_system"] = "appointments"
    if "ingested_at" not in fact.columns:
        fact["ingested_at"] = datetime.now().isoformat()
    
    fact["updated_at"] = datetime.now().isoformat()
    
    # RECONCILIATION
    reconciliation = {
        "rows_before": rows_before,
        "rows_after": len(fact),
        "matched_with_patient": int(fact["patient_birth_date"].notna().sum()),
        "unmatched_patient": int(fact["patient_birth_date"].isna().sum()),
        "matched_with_tarifa": int(fact["tarifa_base"].notna().sum()),
        "unmatched_tarifa": int(fact["tarifa_base"].isna().sum()),
        "duplicated_appointment_id": int(fact["appointment_id"].duplicated().sum()),
        "unique_patients": fact["patient_id"].nunique(),
        "unique_clinics": fact["clinic_code_clean"].nunique(),
        "unique_specialties": fact["specialty_clean"].nunique() if "specialty_clean" in fact.columns else 0,
        "total_revenue": float(fact["amount_charged_clean"].sum()),
        "avg_revenue_gap": float(fact["revenue_gap"].mean()) if fact["revenue_gap"].notna().any() else 0,
        "no_show_count": int(fact["is_no_show"].sum()),
        "peak_hour_count": int(fact["is_peak_hour"].sum()),
        "avg_patient_age": float(fact["patient_age_at_visit"].mean()) if fact["patient_age_at_visit"].notna().any() else 0
    }
    
    logging.info("INTEGRATE / RECONCILIATION: %s", reconciliation)
    
    # Advertencias
    if reconciliation["unmatched_patient"] > 0:
        logging.warning(
            "%s citas sin paciente correspondiente (FK missing)",
            reconciliation["unmatched_patient"]
        )
    
    if reconciliation["unmatched_tarifa"] > 0:
        logging.warning(
            "%s citas sin tarifa correspondiente (clinic_code + specialty missing)",
            reconciliation["unmatched_tarifa"]
        )
    
    return fact, reconciliation

"""
BUILD CURATED DATABASE: Procesar datos para crear la base de datos destino
"""
def build_curated_database(config: ETLConfig) -> None:
    output_db_path = config.output_database_path if hasattr(config, 'output_database_path') else config.database_path
    
    # Asegurar que el directorio existe
    output_db_path.parent.mkdir(parents=True, exist_ok=True)
        
    with sqlite3.connect(output_db_path) as conn:
        # TABLA fact_appointments
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.fact_appointments_table} (
                appointment_id TEXT PRIMARY KEY,
                patient_id TEXT,
                clinic_code TEXT,
                clinic_code_clean TEXT,
                specialty TEXT,
                specialty_clean TEXT,
                scheduled_at TEXT,
                duration_min INTEGER,
                status TEXT,
                amount_charged REAL,
                amount_charged_clean REAL,
                payment_method TEXT,
                created_at TEXT,
                patient_birth_date TEXT,
                patient_sex TEXT,
                patient_city TEXT,
                patient_insurance TEXT,
                patient_registered_at TEXT,
                patient_age_at_visit INTEGER,
                tarifa_base REAL,
                revenue_gap REAL,
                scheduled_date TEXT,
                scheduled_hour INTEGER,
                scheduled_day_of_week INTEGER,
                scheduled_month INTEGER,
                is_peak_hour INTEGER,
                duration_hours REAL,
                is_no_show INTEGER,
                batch_id TEXT,
                source_system TEXT,
                ingested_at TEXT,
                updated_at TEXT
            )
        """)
        
        # TABLA quarantine
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.quarantine_table} (
                source TEXT,
                batch_id TEXT,
                record_id TEXT,
                reject_reason TEXT,
                ingested_at TEXT
            )
        """)
        
        # TABLA etl_runs (auditoría)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.audit_table} (
                run_id TEXT PRIMARY KEY,
                started_at TEXT,
                finished_at TEXT,
                watermark_before TEXT,
                watermark_after TEXT,
                source_appointments INTEGER,
                valid_appointments INTEGER,
                quarantined_appointments INTEGER,
                inserted INTEGER,
                updated INTEGER,
                quality_status TEXT,
                status TEXT,
                error_message TEXT
            )
        """)
        
        # Index para eficientar procesos
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_fact_patient_id 
            ON {config.fact_appointments_table}(patient_id)
        """)
        
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_fact_clinic_code 
            ON {config.fact_appointments_table}(clinic_code_clean)
        """)
        
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_fact_scheduled_date 
            ON {config.fact_appointments_table}(scheduled_date)
        """)
        
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_fact_status 
            ON {config.fact_appointments_table}(status)
        """)
        
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_quarantine_batch 
            ON {config.quarantine_table}(batch_id)
        """)
        
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_audit_run 
            ON {config.audit_table}(run_id)
        """)
        
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        logging.info("BUILD: Tablas creadas/verificadas: %s", [t[0] for t in tables])
    
    logging.info("BUILD: Base de datos lista en %s", output_db_path)



"""
QUALITY GATE: Verificar la calidad de los datos antes de cargarlos
"""
def quality_gate(
    fact_appointments: pd.DataFrame, 
    reconciliation: dict, 
    config: ETLConfig
) -> dict:
    total = reconciliation["rows_after"]
    if total == 0:
        logging.info("QUALITY GATE: sin filas nuevas que evaluar (no hay datos incrementales)")
        return {"status": "PASS", "metrics": {}, "failures": []}
    
    # Métricas de calidad
    
    # Completitud: columnas críticas no deben ser nulas
    required_cols = [
        "appointment_id", "patient_id", "clinic_code_clean", 
        "status", "scheduled_at", "created_at"
    ]
    
    available_cols = [col for col in required_cols if col in fact_appointments.columns]
    if available_cols:
        completeness = fact_appointments[available_cols].notna().all(axis=1).mean()
    else:
        completeness = 0.0
    
    # Tasa de duplicados
    duplicate_rate = reconciliation.get("duplicated_appointment_id", 0) / total if total > 0 else 0
    
    # Tasa de pacientes sin match
    unmatched_patient_rate = reconciliation.get("unmatched_patient", 0) / total if total > 0 else 0
    
    # Tasa de tarifas sin match
    unmatched_tarifa_rate = reconciliation.get("unmatched_tarifa", 0) / total if total > 0 else 0
    
    # Tasa de no-shows
    no_show_rate = reconciliation.get("no_show_count", 0) / total if total > 0 else 0
    
    # Porcentaje de revenue_gap negativo
    negative_gap_rate = 0
    if "revenue_gap" in fact_appointments.columns:
        negative_gaps = (fact_appointments["revenue_gap"] < 0).sum()
        negative_gap_rate = negative_gaps / total if total > 0 else 0
    
    metrics = {
        "total_rows": total,
        "completeness": round(completeness, 4),
        "duplicate_rate": round(duplicate_rate, 4),
        "unmatched_patient_rate": round(unmatched_patient_rate, 4),
        "unmatched_tarifa_rate": round(unmatched_tarifa_rate, 4),
        "no_show_rate": round(no_show_rate, 4),
        "negative_gap_rate": round(negative_gap_rate, 4),
        "avg_patient_age": reconciliation.get("avg_patient_age", 0),
        "total_revenue": reconciliation.get("total_revenue", 0),
        "unique_patients": reconciliation.get("unique_patients", 0),
        "unique_clinics": reconciliation.get("unique_clinics", 0),
        "unique_specialties": reconciliation.get("unique_specialties", 0)
    }
    
    # Evaluación

    failures = []
    
    # Completitud mínima
    completeness_min = config.completeness_min if hasattr(config, 'completeness_min') else 0.70
    if completeness < completeness_min:
        failures.append(f"completeness ({completeness:.2%} < {completeness_min:.2%})")
    
    # Tasa de duplicados máxima
    duplicate_max = config.duplicate_rate_max if hasattr(config, 'duplicate_rate_max') else 0.05
    if duplicate_rate > duplicate_max:
        failures.append(f"duplicate_rate ({duplicate_rate:.2%} > {duplicate_max:.2%})")
    
    # Tasa de pacientes sin match
    null_fk_max = config.null_foreign_key_max if hasattr(config, 'null_foreign_key_max') else 0.10
    if unmatched_patient_rate > null_fk_max:
        failures.append(f"unmatched_patient_rate ({unmatched_patient_rate:.2%} > {null_fk_max:.2%})")
    
    # Tasa de tarifas sin match
    invalid_amount_max = config.invalid_amount_max if hasattr(config, 'invalid_amount_max') else 0.05
    if unmatched_tarifa_rate > invalid_amount_max:
        failures.append(f"unmatched_tarifa_rate ({unmatched_tarifa_rate:.2%} > {invalid_amount_max:.2%})")
    
    # Tasa de revenue_gap negativo
    max_rule_violation = config.max_rule_violation_pct if hasattr(config, 'max_rule_violation_pct') else 0.15
    if negative_gap_rate > max_rule_violation:
        failures.append(f"negative_gap_rate ({negative_gap_rate:.2%} > {max_rule_violation:.2%})")
    
    # Clasificación
    status = "FAIL" if failures else "PASS"
    
    logging.info("QUALITY GATE: status=%s metrics=%s", status, metrics)
    if failures:
        logging.error("QUALITY GATE: umbrales incumplidos: %s", failures)
    
    return {
        "status": status, 
        "metrics": metrics, 
        "failures": failures
    }

"""
LOAD: Subir los datos procesados (y que no se enucentren ya en la BD con UPSERT)
"""
def load(
    config: ETLConfig, 
    fact_appointments: pd.DataFrame, 
    quarantine_df: pd.DataFrame, 
    batch_id: str
) -> tuple[int, int]:
    inserted = 0
    updated = 0
    
    output_db_path = config.output_database_path if hasattr(config, 'output_database_path') else config.database_path
    
    with sqlite3.connect(output_db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        
        if config.fact_appointments_table not in table_names:
            logging.error("LOAD: Tabla %s no existe. Ejecuta build_curated_database primero.", 
                         config.fact_appointments_table)
            raise ValueError(f"Tabla {config.fact_appointments_table} no existe")
        
        try:
            with conn:
                for _, row in fact_appointments.iterrows():
                    cur = conn.execute(
                        f"SELECT 1 FROM {config.fact_appointments_table} WHERE appointment_id = ?",
                        (row["appointment_id"],)
                    )
                    exists = cur.fetchone() is not None
                    
                    def clean_value(val):
                        if pd.isna(val):
                            return None
                        if isinstance(val, (pd.Timestamp, datetime)):
                            return val.isoformat() if hasattr(val, 'isoformat') else str(val)
                        return val
                    
                    conn.execute(f"""
                        INSERT INTO {config.fact_appointments_table}
                        (appointment_id, patient_id, clinic_code, clinic_code_clean, 
                         specialty, specialty_clean, scheduled_at, duration_min, 
                         status, amount_charged, amount_charged_clean, payment_method, 
                         created_at, patient_birth_date, patient_sex, patient_city, 
                         patient_insurance, patient_registered_at, patient_age_at_visit, 
                         tarifa_base, revenue_gap, scheduled_date, scheduled_hour, 
                         scheduled_day_of_week, scheduled_month, is_peak_hour, 
                         duration_hours, is_no_show, batch_id, source_system, 
                         ingested_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(appointment_id) DO UPDATE SET
                            patient_id=excluded.patient_id,
                            clinic_code=excluded.clinic_code,
                            clinic_code_clean=excluded.clinic_code_clean,
                            specialty=excluded.specialty,
                            specialty_clean=excluded.specialty_clean,
                            scheduled_at=excluded.scheduled_at,
                            duration_min=excluded.duration_min,
                            status=excluded.status,
                            amount_charged=excluded.amount_charged,
                            amount_charged_clean=excluded.amount_charged_clean,
                            payment_method=excluded.payment_method,
                            created_at=excluded.created_at,
                            patient_birth_date=excluded.patient_birth_date,
                            patient_sex=excluded.patient_sex,
                            patient_city=excluded.patient_city,
                            patient_insurance=excluded.patient_insurance,
                            patient_registered_at=excluded.patient_registered_at,
                            patient_age_at_visit=excluded.patient_age_at_visit,
                            tarifa_base=excluded.tarifa_base,
                            revenue_gap=excluded.revenue_gap,
                            scheduled_date=excluded.scheduled_date,
                            scheduled_hour=excluded.scheduled_hour,
                            scheduled_day_of_week=excluded.scheduled_day_of_week,
                            scheduled_month=excluded.scheduled_month,
                            is_peak_hour=excluded.is_peak_hour,
                            duration_hours=excluded.duration_hours,
                            is_no_show=excluded.is_no_show,
                            batch_id=excluded.batch_id,
                            source_system=excluded.source_system,
                            ingested_at=excluded.ingested_at,
                            updated_at=excluded.updated_at
                    """, (
                        clean_value(row.get("appointment_id")),
                        clean_value(row.get("patient_id")),
                        clean_value(row.get("clinic_code")),
                        clean_value(row.get("clinic_code_clean")),
                        clean_value(row.get("specialty")),
                        clean_value(row.get("specialty_clean")),
                        clean_value(row.get("scheduled_at")),
                        clean_value(row.get("duration_min")),
                        clean_value(row.get("status")),
                        clean_value(row.get("amount_charged")),
                        clean_value(row.get("amount_charged_clean")),
                        clean_value(row.get("payment_method")),
                        clean_value(row.get("created_at")),
                        clean_value(row.get("patient_birth_date")),
                        clean_value(row.get("patient_sex")),
                        clean_value(row.get("patient_city")),
                        clean_value(row.get("patient_insurance")),
                        clean_value(row.get("patient_registered_at")),
                        clean_value(row.get("patient_age_at_visit")),
                        clean_value(row.get("tarifa_base")),
                        clean_value(row.get("revenue_gap")),
                        clean_value(row.get("scheduled_date")),
                        clean_value(row.get("scheduled_hour")),
                        clean_value(row.get("scheduled_day_of_week")),
                        clean_value(row.get("scheduled_month")),
                        clean_value(row.get("is_peak_hour")),
                        clean_value(row.get("duration_hours")),
                        clean_value(row.get("is_no_show")),
                        clean_value(batch_id),
                        clean_value(row.get("source_system")),
                        clean_value(row.get("ingested_at")),
                        clean_value(datetime.now().isoformat())
                    ))
                    
                    if exists:
                        updated += 1
                    else:
                        inserted += 1
                
                # Cuarentena
                if len(quarantine_df) > 0:
                    quarantine_to_load = quarantine_df.copy()
                    if "record_id" not in quarantine_to_load.columns:
                        quarantine_to_load["record_id"] = "unknown"
                    if "ingested_at" not in quarantine_to_load.columns:
                        quarantine_to_load["ingested_at"] = datetime.now().isoformat()
                    
                    cols = ["source", "batch_id", "record_id", "reject_reason", "ingested_at"]
                    quarantine_to_load = quarantine_to_load[cols]
                    
                    quarantine_to_load.to_sql(
                        config.quarantine_table, 
                        conn, 
                        if_exists="append", 
                        index=False
                    )
                    logging.info("LOAD: %s registros en cuarentena", len(quarantine_to_load))
                    
        except Exception as e:
            logging.error("LOAD: error durante la transaccion, se hace ROLLBACK: %s", e)
            raise
    
    logging.info(
        "LOAD: %s insertados, %s actualizados (UPSERT) en %s",
        inserted, 
        updated, 
        config.fact_appointments_table
    )
    
    return inserted, updated

"""
AUDIT: Guarda la evidencia del proceso completo de ETL en la tabla de auditoría
"""
def audit(
    config: ETLConfig,
    run_id: str,
    started_at: str,
    finished_at: str,
    watermark_before: str,
    watermark_after: str,
    counts: dict,
    status: str,
    error_message: str = None,
) -> None:
    output_db_path = config.output_database_path if hasattr(config, 'output_database_path') else config.database_path
    
    with sqlite3.connect(output_db_path) as conn:
        # Crear tabla si no existe
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.audit_table} (
                run_id TEXT PRIMARY KEY,
                started_at TEXT,
                finished_at TEXT,
                watermark_before TEXT,
                watermark_after TEXT,
                source_appointments INTEGER,
                valid_appointments INTEGER,
                quarantined_appointments INTEGER,
                inserted INTEGER,
                updated INTEGER,
                quality_status TEXT,
                status TEXT,
                error_message TEXT
            )
        """)
        
        # Insertar o reemplazar registro
        with conn:
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {config.audit_table} 
                (run_id, started_at, finished_at, watermark_before, watermark_after,
                 source_appointments, valid_appointments, quarantined_appointments,
                 inserted, updated, quality_status, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    started_at,
                    finished_at,
                    watermark_before,
                    watermark_after,
                    counts.get("source_appointments", 0),
                    counts.get("valid_appointments", 0),
                    counts.get("quarantined_appointments", 0),
                    counts.get("inserted", 0),
                    counts.get("updated", 0),
                    counts.get("quality_status", "UNKNOWN"),
                    status,
                    error_message
                )
            )
    
    logging.info("AUDIT: run_id=%s status=%s registrado en %s", run_id, status, config.audit_table)


def main() -> None:
    """Ejecuta el pipeline ETL completo"""
    
    config = load_config(CONFIG_PATH)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    started_at = datetime.now().isoformat()
    watermark_before = read_watermark(config.watermark_path)
    error_message = None
    
    if hasattr(config, 'log_file_path'):
        setup_logging(config.log_file_path)
    
    logging.info("="*60)
    logging.info("ETL COMPLETO iniciado")
    logging.info("run_id=%s batch_id=%s", run_id, batch_id)
    logging.info("watermark_before=%s", watermark_before)
    logging.info("="*60)

    
    # BUILD: Crear base de datos destino
    try:
        logging.info("BUILD: Creando base de datos destino...")
        build_curated_database(config)
        logging.info("BUILD: Base de datos lista")
    except Exception as e:
        error_message = f"BUILD falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": 0, "valid_appointments": 0, 
             "quarantined_appointments": 0, "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    

    # EXTRACT
    try:
        logging.info("EXTRACT: Extrayendo datos...")
        patients_df, appointments_df, tarifas_df, catalogo = extract(config, watermark_before)
        logging.info("EXTRACT: %s pacientes, %s citas, %s tarifas",
                    len(patients_df), len(appointments_df), len(tarifas_df))
    except Exception as e:
        error_message = f"EXTRACT falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": 0, "valid_appointments": 0, 
             "quarantined_appointments": 0, "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    
    if appointments_df.empty:
        logging.info("Sin citas nuevas desde el watermark: se registra corrida vacia (incremental correcto)")
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": 0, "valid_appointments": 0, 
             "quarantined_appointments": 0, "inserted": 0, "updated": 0,
             "quality_status": "PASS"},
            "SUCCESS_EMPTY",
            None
        )
        logging.info("=== ETL COMPLETO finalizado (sin datos nuevos) ===")
        return
    

    # STAGE
    try:
        logging.info("STAGE: Aplicando stage...")
        patients_staged, appointments_staged, tarifas_staged = stage(
            patients_df, appointments_df, tarifas_df, batch_id
        )
        logging.info("STAGE: batch_id=%s asignado", batch_id)
    except Exception as e:
        error_message = f"STAGE falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), "valid_appointments": 0, 
             "quarantined_appointments": 0, "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    

    # VALIDATE
    try:
        logging.info("VALIDATE: Validando datos...")
        valid_patients, valid_appointments, valid_tarifas, quarantine = validate(
            patients_staged, appointments_staged, tarifas_staged, config
        )
        logging.info("VALIDATE: %s pacientes, %s citas, %s tarifas válidas",
                    len(valid_patients), len(valid_appointments), len(valid_tarifas))
        logging.info("VALIDATE: %s registros en cuarentena", len(quarantine))
    except Exception as e:
        error_message = f"VALIDATE falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), "valid_appointments": 0, 
             "quarantined_appointments": len(quarantine) if 'quarantine' in locals() else 0, 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    
    if valid_appointments.empty:
        logging.warning("Todas las citas del batch fueron a cuarentena: no hay nada que cargar")
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": 0, 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "SUCCESS_EMPTY",
            None
        )
        logging.info("=== ETL COMPLETO finalizado (todos los registros en cuarentena) ===")
        return
    

    # TRANSFORM
    try:
        logging.info("TRANSFORM: Transformando datos...")
        transformed_patients, transformed_appointments, transformed_tarifas = transform(
            valid_patients, valid_appointments, valid_tarifas, config
        )
        logging.info("TRANSFORM: Datos transformados")
    except Exception as e:
        error_message = f"TRANSFORM falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": len(valid_appointments), 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    

    # INTEGRATE
    try:
        logging.info("INTEGRATE: Integrando datos...")
        fact_appointments, reconciliation = integrate(
            transformed_patients, transformed_appointments, transformed_tarifas, config
        )
        logging.info("INTEGRATE: %s filas integradas", len(fact_appointments))
        logging.info("INTEGRATE / RECONCILIATION: %s", reconciliation)
    except Exception as e:
        error_message = f"INTEGRATE falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": len(valid_appointments), 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    

    # QUALITY GATE
    try:
        logging.info("QUALITY GATE: Evaluando calidad...")
        quality_result = quality_gate(fact_appointments, reconciliation, config)
        logging.info("QUALITY GATE: status=%s", quality_result["status"])
        if quality_result['failures']:
            logging.warning("QUALITY GATE: umbrales incumplidos: %s", quality_result['failures'])
    except Exception as e:
        error_message = f"QUALITY GATE falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": len(valid_appointments), 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    
    if quality_result["status"] == "FAIL":
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": len(valid_appointments), 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": "FAIL"},
            "FAILED_QUALITY_GATE",
            f"Umbrales incumplidos: {quality_result['failures']}"
        )
        logging.error("Pipeline detenido: la calidad de los datos no cumple los umbrales definidos")
        logging.error("Fallos: %s", quality_result['failures'])
        raise SystemExit("Pipeline detenido: quality gate falló")
    

    # LOAD
    try:
        logging.info("LOAD: Cargando datos...")
        inserted, updated = load(config, fact_appointments, quarantine, batch_id)
        logging.info("LOAD: %s insertados, %s actualizados", inserted, updated)
    except Exception as e:
        error_message = f"LOAD falló: {str(e)}"
        logging.error(error_message)
        finished_at = datetime.now().isoformat()
        audit(
            config, run_id, started_at, finished_at,
            watermark_before, watermark_before,
            {"source_appointments": len(appointments_df), 
             "valid_appointments": len(valid_appointments), 
             "quarantined_appointments": len(quarantine), 
             "inserted": 0, "updated": 0,
             "quality_status": quality_result["status"]},
            "FAIL",
            error_message
        )
        raise SystemExit(f"Pipeline detenido: {error_message}")
    

    # ACTUALIZAR WATERMARK
    try:
        watermark_after = str(fact_appointments["created_at"].max())
        if watermark_after and watermark_after != 'NaT':
            write_watermark(config.watermark_path, watermark_after)
            logging.info("AUDIT: Watermark actualizado: %s -> %s", watermark_before, watermark_after)
        else:
            watermark_after = watermark_before
            logging.warning("AUDIT: No se pudo actualizar watermark (sin fechas válidas)")
    except Exception as e:
        logging.warning("AUDIT: Error al actualizar watermark: %s", str(e))
        watermark_after = watermark_before
    

    # AUDIT
    finished_at = datetime.now().isoformat()
    audit(
        config, run_id, started_at, finished_at,
        watermark_before, watermark_after,
        {
            "source_appointments": len(appointments_df),
            "valid_appointments": len(valid_appointments),
            "quarantined_appointments": len(quarantine),
            "inserted": inserted,
            "updated": updated,
            "quality_status": quality_result["status"]
        },
        "SUCCESS",
        None
    )
    

    # RESUMEN
    logging.info("="*60)
    logging.info("ETL COMPLETO finalizado exitosamente")
    logging.info("run_id=%s batch_id=%s", run_id, batch_id)
    logging.info("watermark: %s -> %s", watermark_before, watermark_after)
    logging.info("RESUMEN:")
    logging.info("  - Citas fuente: %s", len(appointments_df))
    logging.info("  - Citas válidas: %s", len(valid_appointments))
    logging.info("  - Citas en cuarentena: %s", len(quarantine))
    logging.info("  - Insertadas: %s", inserted)
    logging.info("  - Actualizadas: %s", updated)
    logging.info("  - Quality Gate: %s", quality_result["status"])
    logging.info("="*60)

if __name__ == "__main__":
    main()