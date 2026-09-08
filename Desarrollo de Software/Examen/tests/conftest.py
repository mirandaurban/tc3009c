import pytest
import sqlite3
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def temp_db():
    """
    Crea una base de datos temporal para pruebas
    """
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE patients (
            patient_id TEXT PRIMARY KEY,
            birth_date TEXT,
            sex TEXT,
            city TEXT,
            insurance TEXT,
            registered_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE appointments (
            appointment_id TEXT PRIMARY KEY,
            patient_id TEXT,
            clinic_code TEXT,
            specialty TEXT,
            scheduled_at TEXT,
            duration_min INTEGER,
            status TEXT,
            amount_charged REAL,
            payment_method TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config(temp_db):
    """
    Crea un archivo de configuracion de prueba
    """
    temp_dir = temp_db.parent
    
    config = {
        "paths": {
            "database": str(temp_db),
            "tarifas": str(temp_dir / "tarifas_especialidad.csv"),
            "catalogo": str(temp_dir / "catalogo_clinicas.json"),
            "profile": str(temp_dir / "data_profile.json"),
            "watermark": str(temp_dir / "watermark.json"),
            "output_database": str(temp_dir / "clinica_curated.db"),
            "log_file": str(temp_dir / "etl.log")
        },
        "output_tables": {
            "fact_appointments": "fact_appointments",
            "quarantine": "quarantine",
            "audit": "etl_runs"
        },
        "quality_thresholds": {
            "completeness_min": 0.70,
            "duplicate_rate_max": 0.10,
            "null_foreign_key_max": 0.15,
            "invalid_amount_max": 0.15,
            "max_rule_violation_pct": 0.65
        },
        "allowed_statuses": ["completada", "no_show", "cancelada"],
        "allowed_payment_methods": ["efectivo", "tarjeta", "transferencia", "aseguradora"],
        "defect_probabilities": {
            "D1_orphan_fk": 0.02,
            "D2_invalid_amount": 0.01,
            "D3_null_relevant": 0.03,
            "D4_duplicates": 0.02,
            "D5_nomenclature": 0.05,
            "D6_silent_defect": 0.04,
            "D7_impossible_rule": 0.005
        }
    }
    
    config_path = temp_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    # Crear catalogo
    catalogo = {
        "clinicas": [
            {
                "clinic_code": "CL01",
                "nombre": "SaludNorte Centro",
                "ciudad": "Monterrey",
                "zona": "norte",
                "aliases": ["CL-01", "cl01", "Clinica Centro"]
            },
            {
                "clinic_code": "CL02",
                "nombre": "Hospital Sur",
                "ciudad": "Guadalajara",
                "zona": "sur",
                "aliases": ["CL-02", "cl02", "Hospital del Sur"]
            }
        ],
        "especialidad_aliases": {
            "Medicina General": ["med gral", "MEDICINA_GENERAL", "MG", "med-general"],
            "Pediatria": ["pediatria", "PEDIATRIA", "PED", "ped"],
            "Traumatologia": ["traumatologia", "TRAUMA", "TRA", "trauma"]
        }
    }
    
    with open(temp_dir / "catalogo_clinicas.json", "w") as f:
        json.dump(catalogo, f)
    
    # Crear tarifas
    tarifas = pd.DataFrame({
        'clinic_code': ['CL01', 'CL01', 'CL02'],
        'specialty': ['Medicina General', 'Traumatologia', 'Pediatria'],
        'tarifa_base': [500, 700, 600],
        'moneda': ['MXN', 'MXN', 'MXN'],
        'vigencia_desde': ['2024-01-01', '2024-01-01', '2024-01-01']
    })
    tarifas.to_csv(temp_dir / "tarifas_especialidad.csv", index=False)
    
    return config_path


@pytest.fixture
def sample_patients():
    """
    Datos de muestra para pacientes
    """
    return pd.DataFrame({
        'patient_id': ['P000001', 'P000002', 'P000003'],
        'birth_date': ['1990-01-15', '1985-06-20', '2000-03-10'],
        'sex': ['F', 'M', 'F'],
        'city': ['Monterrey', 'CDMX', 'Guadalajara'],
        'insurance': ['basico', 'ninguno', 'premium'],
        'registered_at': ['2023-01-01', '2023-02-01', '2023-03-01']
    })


@pytest.fixture
def sample_appointments():
    """
    Datos de muestra para citas
    """
    return pd.DataFrame({
        'appointment_id': ['A0000001', 'A0000002', 'A0000003'],
        'patient_id': ['P000001', 'P000002', 'P000003'],
        'clinic_code': ['CL01', 'CL02', 'CL01'],
        'specialty': ['Medicina General', 'Pediatria', 'Traumatologia'],
        'scheduled_at': ['2024-01-15 10:00:00', '2024-01-16 11:30:00', '2024-01-17 09:00:00'],
        'duration_min': [30, 20, 45],
        'status': ['completada', 'no_show', 'cancelada'],
        'amount_charged': [500.0, 0.0, 0.0],
        'payment_method': ['efectivo', 'tarjeta', 'transferencia'],
        'created_at': ['2024-01-10 08:00:00', '2024-01-11 09:00:00', '2024-01-12 10:00:00']
    })