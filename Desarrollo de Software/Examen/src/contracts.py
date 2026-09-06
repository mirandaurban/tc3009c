"""
DEFINE: Contratos de datos y esquemas para configuracion del pipeline

Basado en el diccionario de datos 'docs/data_dictionary.md'. Se definen los esquemas, validaciones y reglas de negocio
que el ETL debe aplicar a los datos de entrada y salida.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re


# Especialidades válidas
VALID_SPECIALTIES = [
    "Medicina General", "Pediatría", "Traumatología", "Cardiología",
    "Dermatología", "Ginecología", "Odontología", "Oftalmología"
]

# Clínicas válidas
VALID_CLINIC_CODES = ["CL01", "CL02", "CL03", "CL04", "CL05"]

# Ciudades válidas
VALID_CITIES = ["Monterrey", "Guadalajara", "CDMX", "Puebla", "Tijuana", "Cancún"]

# Seguros válidos
VALID_INSURANCE = ["ninguno", "basico", "premium"]

# Estados válidos
VALID_STATUSES = ["completada", "no_show", "cancelada"]

# Métodos de pago válidos
VALID_PAYMENT_METHODS = ["efectivo", "tarjeta", "transferencia", "aseguradora"]

# Duraciones válidas
VALID_DURATIONS = [15, 20, 30, 45, 60]

# Monedas válidas
VALID_CURRENCIES = ["MXN"]

# Rangos de fechas (para validación)
PATIENT_BIRTH_RANGE = ("1940-01-01", "2015-12-31")
PATIENT_REGISTERED_RANGE = ("2022-01-01", "2024-12-31")
APPOINTMENT_SCHEDULED_RANGE = ("2024-01-01", "2025-11-30")
APPOINTMENT_CREATED_RANGE = ("2024-01-01", "2025-12-31")
TARIFA_VIGENCIA_VALUES = ["2024-01-01", "2025-01-01"]


"""
DATA CLASSES PARA CONTRATOS (PURO DOMINIO)
"""
@dataclass
class ColumnContract:
    """Contrato por columna"""
    name: str
    dtype: str
    nullable: bool = False
    description: str = ""
    valid_values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    regex_pattern: Optional[str] = None
    format: Optional[str] = None
    fk: Optional[str] = None  # Referencia a otra tabla
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class TableContract:
    """Contrato por tabla"""
    name: str
    columns: List[ColumnContract]
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[Dict[str, str]]] = None
    description: str = ""
    expected_rows: Optional[int] = None

# Tabla: patients
PATIENTS_CONTRACT = TableContract(
    name="patients",
    description="Tabla de pacientes del sistema",
    columns=[
        ColumnContract("patient_id", "TEXT", False, 
                      "ID único del paciente (P + 6 dígitos)",
                      regex_pattern=r"^P\d{6}$"),
        ColumnContract("birth_date", "TEXT", False, 
                      "Fecha de nacimiento (YYYY-MM-DD)",
                      format="YYYY-MM-DD"),
        ColumnContract("sex", "TEXT", False, "Sexo del paciente",
                      valid_values=["F", "M"]),
        ColumnContract("city", "TEXT", False, "Ciudad de residencia",
                      valid_values=VALID_CITIES),
        ColumnContract("insurance", "TEXT", False, "Tipo de seguro",
                      valid_values=VALID_INSURANCE),
        ColumnContract("registered_at", "TEXT", False, 
                      "Fecha de registro (YYYY-MM-DD)",
                      format="YYYY-MM-DD"),
    ],
    primary_key=["patient_id"],
    expected_rows=8000
)


# Tabla: appointments 
APPOINTMENTS_CONTRACT = TableContract(
    name="appointments",
    description="Tabla de citas médicas",
    columns=[
        ColumnContract("appointment_id", "TEXT", False,
                      "ID único de la cita (A + 7 dígitos)",
                      regex_pattern=r"^A\d{7}$"),
        ColumnContract("patient_id", "TEXT", False,
                      "ID del paciente",
                      fk="patients.patient_id"),
        ColumnContract("clinic_code", "TEXT", False,
                      "Código de la clínica",
                      valid_values=VALID_CLINIC_CODES),
        ColumnContract("specialty", "TEXT", True,
                      "Especialidad médica",
                      valid_values=VALID_SPECIALTIES),
        ColumnContract("scheduled_at", "TEXT", False,
                      "Fecha y hora agendada (YYYY-MM-DD HH:MM:SS)",
                      format="YYYY-MM-DD HH:MM:SS"),
        ColumnContract("duration_min", "INTEGER", False,
                      "Duración en minutos",
                      valid_values=VALID_DURATIONS),
        ColumnContract("status", "TEXT", False,
                      "Estado de la cita",
                      valid_values=VALID_STATUSES),
        ColumnContract("amount_charged", "REAL", True,
                      "Monto cobrado",
                      min_value=0),
        ColumnContract("payment_method", "TEXT", False,
                      "Método de pago",
                      valid_values=VALID_PAYMENT_METHODS),
        ColumnContract("created_at", "TEXT", False,
                      "Fecha de creación (YYYY-MM-DD HH:MM:SS)",
                      format="YYYY-MM-DD HH:MM:SS"),
    ],
    primary_key=["appointment_id"],
    foreign_keys=[{"columns": ["patient_id"], "references": "patients(patient_id)"}],
    expected_rows=60000
)


# Tabla: tarifas
TARIFAS_CONTRACT = TableContract(
    name="tarifas_especialidad",
    description="Tarifas base por clínica y especialidad",
    columns=[
        ColumnContract("clinic_code", "TEXT", False,
                      "Código de la clínica",
                      valid_values=VALID_CLINIC_CODES),
        ColumnContract("specialty", "TEXT", False,
                      "Especialidad médica",
                      valid_values=VALID_SPECIALTIES),
        ColumnContract("tarifa_base", "INTEGER", False,
                      "Tarifa base en MXN (múltiplo de 50)",
                      min_value=450, max_value=2200),
        ColumnContract("moneda", "TEXT", False,
                      "Moneda",
                      valid_values=VALID_CURRENCIES),
        ColumnContract("vigencia_desde", "TEXT", False,
                      "Fecha de vigencia (YYYY-MM-DD)",
                      format="YYYY-MM-DD"),
    ],
    primary_key=["clinic_code", "specialty"],
    expected_rows=40
)

FACT_APPOINTMENTS_CONTRACT = TableContract(
    name="fact_appointments",
    description="Tabla de hechos de citas médicas (curada)",
    columns=[
        # Columnas originales
        ColumnContract("appointment_id", "TEXT", False, "ID único de la cita"),
        ColumnContract("patient_id", "TEXT", False, "ID del paciente"),
        ColumnContract("clinic_code", "TEXT", False, "Código de clínica original"),
        ColumnContract("specialty", "TEXT", True, "Especialidad original"),
        ColumnContract("scheduled_at", "TEXT", False, "Fecha y hora agendada"),
        ColumnContract("duration_min", "INTEGER", False, "Duración en minutos"),
        ColumnContract("status", "TEXT", False, "Estado de la cita"),
        ColumnContract("amount_charged", "REAL", True, "Monto cobrado original"),
        ColumnContract("payment_method", "TEXT", False, "Método de pago"),
        ColumnContract("created_at", "TEXT", False, "Fecha de creación"),
        
        # Columnas homologadas/limpias
        ColumnContract("specialty_clean", "TEXT", True, 
                      "Especialidad homologada (dominio)"),
        ColumnContract("clinic_code_clean", "TEXT", False,
                      "Código de clínica homologado (dominio)"),
        ColumnContract("amount_charged_clean", "REAL", True,
                      "Monto cobrado limpio",
                      min_value=0),
        
        # Variables derivadas
        ColumnContract("patient_age_at_visit", "INTEGER", True,
                      "Edad del paciente en la cita",
                      min_value=0, max_value=120),
        ColumnContract("is_no_show", "INTEGER", False,
                      "Indica si fue no-show (0/1)",
                      valid_values=[0, 1]),
        ColumnContract("tarifa_base", "REAL", True,
                      "Tarifa base de la especialidad",
                      min_value=0),
        ColumnContract("revenue_gap", "REAL", True,
                      "Diferencia amount - tarifa_base"),
        ColumnContract("scheduled_date", "TEXT", True,
                      "Fecha de la cita (YYYY-MM-DD)"),
        ColumnContract("scheduled_hour", "INTEGER", True,
                      "Hora de la cita (0-23)",
                      min_value=0, max_value=23),
        ColumnContract("is_peak_hour", "INTEGER", False,
                      "Indica si es hora pico (9-13)",
                      valid_values=[0, 1]),
        ColumnContract("duration_hours", "REAL", False,
                      "Duración en horas",
                      min_value=0),
        
        # Metadatos de procesamiento
        ColumnContract("defectos_detectados", "TEXT", True,
                      "Defectos detectados (separados por ;)"),
        ColumnContract("batch_id", "TEXT", False, "ID del batch"),
        ColumnContract("updated_at", "TEXT", False, "Fecha de actualización"),
        ColumnContract("source_system", "TEXT", False, "Sistema de origen"),
    ],
    primary_key=["appointment_id"]
)


# Tabla: cuarentena
QUARANTINE_CONTRACT = TableContract(
    name="quarantine",
    description="Tabla de registros rechazados",
    columns=[
        ColumnContract("source", "TEXT", False, "Fuente del registro"),
        ColumnContract("batch_id", "TEXT", False, "ID del batch"),
        ColumnContract("record_id", "TEXT", False, "ID del registro original"),
        ColumnContract("reject_reason", "TEXT", False, "Razón del rechazo"),
        ColumnContract("ingested_at", "TEXT", False, "Fecha de ingesta"),
    ]
)


# Tabla: auditoría
AUDIT_CONTRACT = TableContract(
    name="etl_runs",
    description="Tabla de auditoría del ETL",
    columns=[
        ColumnContract("run_id", "TEXT", False, "ID único de la ejecución"),
        ColumnContract("started_at", "TEXT", False, "Fecha de inicio"),
        ColumnContract("finished_at", "TEXT", True, "Fecha de finalización"),
        ColumnContract("watermark_before", "TEXT", False, "Watermark antes"),
        ColumnContract("watermark_after", "TEXT", True, "Watermark después"),
        ColumnContract("source_appointments", "INTEGER", False, "Citas leídas",
                      min_value=0),
        ColumnContract("valid_appointments", "INTEGER", False, "Citas válidas",
                      min_value=0),
        ColumnContract("quarantined_appointments", "INTEGER", False, "Citas rechazadas",
                      min_value=0),
        ColumnContract("inserted", "INTEGER", False, "Citas insertadas",
                      min_value=0),
        ColumnContract("updated", "INTEGER", False, "Citas actualizadas",
                      min_value=0),
        ColumnContract("quality_status", "TEXT", False, "Estado del quality gate",
                      valid_values=["PASS", "FAIL", "UNKNOWN"]),
        ColumnContract("status", "TEXT", False, "Estado final",
                      valid_values=["SUCCESS", "FAIL", "RUNNING"]),
        ColumnContract("error_message", "TEXT", True, "Mensaje de error"),
    ],
    primary_key=["run_id"]
)

"""
Exportar contratos
"""

ALL_CONTRACTS = {
    "patients": PATIENTS_CONTRACT,
    "appointments": APPOINTMENTS_CONTRACT,
    "tarifas": TARIFAS_CONTRACT,
    "fact_appointments": FACT_APPOINTMENTS_CONTRACT,
    "quarantine": QUARANTINE_CONTRACT,
    "audit": AUDIT_CONTRACT
}