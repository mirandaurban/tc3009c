"""
Archivo para generar los datos iniciales para el sistema.

Produce:
- SQLite: clinica.db (patients, appointments)
- CSV: tarifas_especialidad.csv
- JSON: catalogo_clinicas.json
- JSON: data_profile.json
"""

import json
import sqlite3
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent  # /.../Examen/scripts/
ROOT_DIR = SCRIPT_DIR.parent  # /.../Examen/
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

# Crear directorios si no existen
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Leer configuración inicial
def load_config():
    config_path = ROOT_DIR / "config.json"
    if not config_path.exists():
        print(f"Error: No se encuentra config.json en {config_path}")
        print(f"Directorio actual: {Path.cwd()}")
        print(f"Directorio del script: {SCRIPT_DIR}")
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
SEED = config['seed']
N_PATIENTS = config['n_patients']
N_APPOINTMENTS = config['n_appointments']

# Actualizar paths para que apunten a ../data/
PATHS = {
    "database": DATA_DIR / "clinica.db",
    "tarifas": DATA_DIR / "tarifas_especialidad.csv",
    "catalogo": DATA_DIR / "catalogo_clinicas.json",
    "profile": DATA_DIR / "data_profile.json"
}

# Generador único
rng = np.random.default_rng(SEED)

# Contador de defectos
defect_counts = {f'D{i}': 0 for i in range(1, 8)}

# Definir especialidades y pesos
SPECIALTIES = [
    "Medicina General", "Pediatría", "Traumatología", "Cardiología",
    "Dermatología", "Ginecología", "Odontología", "Oftalmología"
]

# Generar pesos para especialidades 
specialty_weights = rng.uniform(0.05, 0.3, 8)
specialty_weights = specialty_weights / specialty_weights.sum()
while (specialty_weights < 0.05).any():
    for i in range(len(specialty_weights)):
        if specialty_weights[i] < 0.05:
            specialty_weights[i] = 0.05
    specialty_weights = specialty_weights / specialty_weights.sum()

CITIES = ['Monterrey', 'Guadalajara', 'CDMX', 'Puebla', 'Tijuana', 'Cancún']
CITY_WEIGHTS = [0.28, 0.22, 0.18, 0.14, 0.11, 0.07]
CLINIC_CODES = ['CL01', 'CL02', 'CL03', 'CL04', 'CL05']
CLINIC_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

# Definir datos fijos del catálogo
CLINIC_DATA = {
    "CL01": {
        "nombre": "SaludNorte Centro",
        "ciudad": "Monterrey",
        "zona": "norte",
        "aliases": ["CL-01", "cl01", "Clinica Centro", "SaludNorte", "SN01"]
    },
    "CL02": {
        "nombre": "Hospital Sur",
        "ciudad": "Guadalajara",
        "zona": "sur",
        "aliases": ["CL-02", "cl02", "Hospital del Sur", "HS02", "Clinica Sur"]
    },
    "CL03": {
        "nombre": "Centro Médico Central",
        "ciudad": "CDMX",
        "zona": "centro",
        "aliases": ["CL-03", "cl03", "CMC", "Central", "Clinica Central"]
    },
    "CL04": {
        "nombre": "Clínica del Este",
        "ciudad": "Puebla",
        "zona": "este",
        "aliases": ["CL-04", "cl04", "Este", "Clinica Este", "CE04"]
    },
    "CL05": {
        "nombre": "Salud del Oeste",
        "ciudad": "Tijuana",
        "zona": "oeste",
        "aliases": ["CL-05", "cl05", "Oeste", "Clinica Oeste", "SO05"]
    }
}

ESPECIALIDAD_ALIASES = {
    "Medicina General": ["med gral", "MEDICINA_GENERAL", "medicina general ", "MG", "med-general"],
    "Pediatría": ["pediatria", "PEDIATRIA", "pediatría", "PED", "ped"],
    "Traumatología": ["traumatologia", "TRAUMA", "Traumatología", "TRA", "trauma"],
    "Cardiología": ["cardiologia", "CARDIOLOGIA", "Cardiología", "CAR", "cardio"],
    "Dermatología": ["dermatologia", "DERMATOLOGIA", "Dermatología", "DER", "derma"],
    "Ginecología": ["ginecologia", "GINECOLOGIA", "Ginecología", "GIN", "gineco"],
    "Odontología": ["odontologia", "ODONTOLOGIA", "Odontología", "ODO", "odonto"],
    "Oftalmología": ["oftalmologia", "OFTALMOLOGIA", "Oftalmología", "OFT", "oftalmo"]
}


"""
Generación de tablas con sus respectivas especifícaciones
"""

def build_patients():
    """
    Tabla Patients
    """
    patients = []
    start_birth = datetime(1940, 1, 1) # 1940-01-01
    end_birth = datetime(2015, 12, 31) # 2015-12-31
    start_reg = datetime(2022, 1, 1) # 2022-01-01
    end_reg = datetime(2024, 12, 31) # 2024-12-31
    
    for i in range(1, N_PATIENTS + 1):
        patient_id = f"P{i:06d}"

        birth_days = int(rng.integers(0, (end_birth - start_birth).days + 1))
        birth_date = start_birth + timedelta(days=birth_days)
        
        sex = rng.choice(['F', 'M'], p=[0.54, 0.46])
        city = rng.choice(CITIES, p=CITY_WEIGHTS)
        insurance = rng.choice(['ninguno', 'basico', 'premium'], p=[0.45, 0.40, 0.15])
        
        reg_days = int(rng.integers(0, (end_reg - start_reg).days + 1))
        registered_at = start_reg + timedelta(days=reg_days)
        
        patients.append({
            'patient_id': patient_id,
            'birth_date': birth_date.strftime('%Y-%m-%d'),
            'sex': sex,
            'city': city,
            'insurance': insurance,
            'registered_at': registered_at.strftime('%Y-%m-%d')
        })
    
    return patients

def generate_datetime(start_date, end_date):
    """
    Genera fecha y hora para tabla appointments según los requerimientos
    """
    for _ in range(1000):
        day_offset = int(rng.integers(0, (end_date - start_date).days + 1))
        date = start_date + timedelta(days=day_offset)
        
        weekday = date.weekday()
        if weekday == 5:  # Sábado
            if rng.random() > 0.4:
                continue
        elif weekday == 6:  # Domingo
            if rng.random() > 0.05:
                continue
        
        if rng.random() < 0.55:  # 55% entre 9-13
            hour = rng.choice(range(9, 14))
        else:
            hour = rng.choice(range(8, 19))
        
        minute = rng.choice([0, 15, 30, 45])
        if hour == 18 and minute > 45:
            minute = 45
        
        return datetime(date.year, date.month, date.day, hour, minute)
    
    return start_date + timedelta(days=rng.integers(0, 30))


def build_tarifas():
    """
    Tabla Tarifas
    """
    tarifas = []
    
    for clinic in CLINIC_CODES:
        for specialty in SPECIALTIES:
            tarifa_base = int(np.round(int(rng.integers(450, 2200)) / 50) * 50)
            vigencia = '2024-01-01' if rng.random() < 0.8 else '2025-01-01'
            tarifas.append([clinic, specialty, tarifa_base, 'MXN', vigencia])
    
    with open(PATHS['tarifas'], 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['clinic_code', 'specialty', 'tarifa_base', 'moneda', 'vigencia_desde'])
        writer.writerows(tarifas)
    
    return tarifas

def build_appointments(patients, weights, tarifas):
    """
    Tabla Appointments
    """
    appointments = []
    
    # Diccionario de tarifas
    tarifa_dict = {}
    for t in tarifas:
        tarifa_dict[(t[0], t[1])] = t[2]
    
    patient_ids = [p['patient_id'] for p in patients]
    start_date = datetime(2024, 1, 1) # 2024-01-01
    end_date = datetime(2025, 11, 30) # 2025-11-30
    
    for i in range(1, N_APPOINTMENTS + 1):
        appointment_id = f"A{i:07d}"
        
        patient_id = rng.choice(patient_ids, p=weights)
        clinic_code = rng.choice(CLINIC_CODES, p=CLINIC_WEIGHTS)
        specialty = rng.choice(SPECIALTIES, p=specialty_weights)
        
        scheduled_at = generate_datetime(start_date, end_date)
        duration_min = int(rng.choice([15, 20, 30, 45, 60], p=[0.30, 0.25, 0.25, 0.15, 0.05]))
        status = rng.choice(['completada', 'no_show', 'cancelada'], p=[0.78, 0.13, 0.09])
        
        # Monto cobrado
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

        days_offset = int(rng.integers(1, 46))
        created_at = scheduled_at - timedelta(days=days_offset)
        
        appointments.append({
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
    
    return appointments

def build_catalogo():
    """Construye catálogo de clínicas según 3.6"""
    catalogo = {
        "clinicas": [
            {
                "clinic_code": code,
                "nombre": data["nombre"],
                "ciudad": data["ciudad"],
                "zona": data["zona"],
                "aliases": data["aliases"]
            }
            for code, data in CLINIC_DATA.items()
        ],
        "especialidad_aliases": ESPECIALIDAD_ALIASES
    }
    
    with open(PATHS['catalogo'], 'w', encoding='utf-8') as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)

    return catalogo

"""
Modificación de la información creada
"""

def inject_defects(appointments, patients):
    """
    Inyección de defectos a la información creada
    """
    n = len(appointments)
    patient_ids = set(p['patient_id'] for p in patients)
    original_appointments = [dict(a) for a in appointments]
    
    # D1: FK huérfana (2.0%)
    d1_count = int(n * 0.02)
    for i in rng.choice(range(n), size=d1_count, replace=False):
        while True:
            fake_id = f"P9{int(rng.integers(10000, 99999))}"
            if fake_id not in patient_ids:
                appointments[i]['patient_id'] = fake_id
                defect_counts['D1'] += 1
                break
    
    # D2: Monto inválido (1.0%)
    d2_count = int(n * 0.01)
    for i in rng.choice(range(n), size=d2_count, replace=False):
        if rng.random() < 0.5:
            appointments[i]['amount_charged'] = -abs(appointments[i]['amount_charged'])
        else:
            appointments[i]['amount_charged'] = 999999.0
        defect_counts['D2'] += 1
    
    # D3: Nulo relevante (3.0%)
    d3_count = int(n * 0.03)
    for i in rng.choice(range(n), size=d3_count, replace=False):
        if rng.random() < 0.5:
            appointments[i]['specialty'] = None
        else:
            appointments[i]['amount_charged'] = None
        defect_counts['D3'] += 1
    
    # D4: Duplicados (2.0%)
    d4_count = int(n * 0.02)
    for _ in range(d4_count):
        idx = int(rng.integers(0, n))
        dup = dict(original_appointments[idx])
        
        if rng.random() < 0.5:
            # Duplicado exacto
            pass
        else:
            new_id = f"A{int(rng.integers(1000000, 9999999)):07d}"
            dup['appointment_id'] = new_id
            dup['amount_charged'] = round(dup['amount_charged'] * rng.uniform(0.5, 1.5), 2)
            if dup['amount_charged'] == 0 and rng.random() < 0.5:
                dup['amount_charged'] = 100.0
        
        appointments.append(dup)
        defect_counts['D4'] += 1
    
    # D5: Nomenclatura (5.0%)
    with open(PATHS['catalogo'], 'r', encoding='utf-8') as f:
        catalogo = json.load(f)
        alias_map = catalogo['especialidad_aliases']
    
    d5_count = int(len(appointments) * 0.05)
    for i in rng.choice(range(len(appointments)), size=d5_count, replace=False):
        current_specialty = appointments[i]['specialty']
        if current_specialty in alias_map:
            aliases = alias_map[current_specialty]
            if aliases:
                appointments[i]['specialty'] = rng.choice(aliases)
                defect_counts['D5'] += 1
    
    # D6: Defecto silencioso (4.0%)
    d6_count = int(len(appointments) * 0.04)
    for i in rng.choice(range(len(appointments)), size=d6_count, replace=False):
        if rng.random() < 0.5:
            appointments[i]['clinic_code'] = f" 'CL{int(rng.integers(1, 6)):02d}' "
        else:
            original_date = datetime.strptime(appointments[i]['scheduled_at'], '%Y-%m-%d %H:%M:%S')
            if rng.random() < 0.5:
                appointments[i]['scheduled_at'] = original_date.strftime('%m/%d/%Y %H:%M')
            else:
                appointments[i]['scheduled_at'] = original_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        defect_counts['D6'] += 1
    
    # D7: Regla física imposible (0.5%)
    d7_count = int(len(appointments) * 0.005)
    for i in rng.choice(range(len(appointments)), size=d7_count, replace=False):
        if rng.random() < 0.5:
            appointments[i]['duration_min'] = 0
            if appointments[i]['amount_charged'] is None:
                appointments[i]['amount_charged'] = 500.0
            else:
                appointments[i]['amount_charged'] = max(1.0, appointments[i]['amount_charged'])
        else:
            patient_id = appointments[i]['patient_id']
            patient = next((p for p in patients if p['patient_id'] == patient_id), None)
            if patient:
                reg_date = datetime.strptime(patient['registered_at'], '%Y-%m-%d')
                offset = int(rng.integers(1, 11))
                new_date = reg_date - timedelta(days=offset)
                appointments[i]['scheduled_at'] = new_date.strftime('%Y-%m-%d %H:%M:%S')
        defect_counts['D7'] += 1
    
    return appointments


"""
Inyección a la BD de los datos creados
"""
def create_database(patients, appointments):
    """
    Crea la base de datos SQLite
    """
    if os.path.exists(PATHS['database']):
        os.remove(PATHS['database'])
    
    conn = sqlite3.connect(PATHS['database'])
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE patients (
            patient_id TEXT PRIMARY KEY,
            birth_date TEXT,
            sex TEXT,
            city TEXT,
            insurance TEXT,
            registered_at TEXT
        )
    ''')
    
    for p in patients:
        cursor.execute('''
            INSERT INTO patients (patient_id, birth_date, sex, city, insurance, registered_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (p['patient_id'], p['birth_date'], p['sex'], p['city'], p['insurance'], p['registered_at']))
    
    cursor.execute('''
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
            created_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    ''')
    
    for a in appointments:
        cursor.execute('''
            INSERT OR REPLACE INTO appointments (
                appointment_id, patient_id, clinic_code, specialty, 
                scheduled_at, duration_min, status, amount_charged, 
                payment_method, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            a['appointment_id'], a['patient_id'], a['clinic_code'],
            a['specialty'], a['scheduled_at'], a['duration_min'],
            a['status'], a['amount_charged'], a['payment_method'],
            a['created_at']
        ))
    
    conn.commit()
    conn.close()

"""
Otras funciones relevantes
"""
def create_profile(patients, appointments):
    """
    Manifiesto de verificación
    """
    profile = {
        'seed': SEED,
        'n_patients': len(patients),
        'n_appointments': len(appointments),
        'defect_counts': defect_counts,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(PATHS['profile'], 'w') as f:
        json.dump(profile, f, indent=2)


def verify_checks(patients, appointments):
    """
    Verificar los checks de aceptación
    """
    print("\n=== Checks de Aceptación ===")
    
    # 1. Verificar número de pacientes
    assert len(patients) == N_PATIENTS, f"Se esperaban {N_PATIENTS} pacientes"
    assert len(set(p['patient_id'] for p in patients)) == N_PATIENTS
    print(f"✓ patients = {N_PATIENTS} filas y patient_id único")
    
    # 2. Verificar número de citas
    assert len(appointments) >= N_APPOINTMENTS
    print(f"✓ appointments ≥ {N_APPOINTMENTS} filas ({len(appointments)} filas)")
    
    # 3. Verificar skew de pacientes
    patient_counts = {}
    for a in appointments:
        patient_counts[a['patient_id']] = patient_counts.get(a['patient_id'], 0) + 1
    
    sorted_counts = sorted(patient_counts.values(), reverse=True)
    n_patients = len(sorted_counts)
    top_30 = int(n_patients * 0.3)
    top_30_total = sum(sorted_counts[:top_30])
    total_appointments = sum(sorted_counts)
    percentage = (top_30_total / total_appointments) * 100
    
    print(f"Top 20%: {(sum(sorted_counts[:int(n_patients*0.2)])/total_appointments)*100:.1f}%")
    print(f"Top 30%: {percentage:.1f}%")
    print(f"Top 50%: {(sum(sorted_counts[:int(n_patients*0.5)])/total_appointments)*100:.1f}%")
    
    assert 65 <= percentage <= 75
    print(f"✓ % de citas del top 30% de pacientes: {percentage:.1f}% (65-75%)")
    
    # 4. Verificar defectos
    expected = {'D1': 0.02, 'D2': 0.01, 'D3': 0.03, 'D4': 0.02, 'D5': 0.05, 'D6': 0.04, 'D7': 0.005}
    print("\nConteo de defectos:")
    for defect_id, exp in expected.items():
        actual = defect_counts[defect_id] / len(appointments)
        diff = abs(actual - exp)
        status = "✓" if diff <= 0.003 else "⚠"
        print(f"  {status} {defect_id}: {actual*100:.2f}% (esperado {exp*100:.2f}%)")
    
    # 5. Verificar CSV
    with open(PATHS['tarifas'], 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 41  # header + 40
        for row in rows[1:]:
            assert row[2] != ''
    print("✓ CSV tiene exactamente 40 filas y ninguna tarifa nula")
    
    # 6. Verificar clinic codes
    with open(PATHS['catalogo'], 'r') as f:
        catalogo = json.load(f)
        clinic_codes = [c['clinic_code'] for c in catalogo['clinicas']]
    
    appointments_clinics = set()
    for a in appointments:
        code = str(a['clinic_code']).strip()
        if code.startswith("'") and code.endswith("'"):
            code = code[1:-1].strip()
        appointments_clinics.add(code)
    
    for code in clinic_codes:
        assert code in appointments_clinics or any(code in str(a['clinic_code']) for a in appointments)
    print("✓ Todo clinic_code del catálogo aparece en appointments")
    
    print("\n✓ Todos los checks de aceptación se aprobaron")

def generate_data_dictionary():
    """Genera el diccionario de datos en docs/data_dictionary.md"""
    
    md_content = """# Diccionario de Datos - Sistema de Citas Médicas

## Fuente 1: SQLite - Tabla `patients` (clinica.db)

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| patient_id | TEXT | Formato P000001 a P008000, único | No | Generado por seed_database.py | - |
| birth_date | TEXT (YYYY-MM-DD) | 1940-01-01 a 2015-12-31 | No | Generado por seed_database.py | - |
| sex | TEXT | 'F' o 'M' | No | Generado por seed_database.py | - |
| city | TEXT | """ + ", ".join(CITIES) + """ | No | Generado por seed_database.py | - |
| insurance | TEXT | 'ninguno', 'basico', 'premium' | No | Generado por seed_database.py | - |
| registered_at | TEXT (YYYY-MM-DD) | 2022-01-01 a 2024-12-31 | No | Generado por seed_database.py | - |

## Fuente 1: SQLite - Tabla `appointments` (clinica.db)

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| appointment_id | TEXT | Formato A0000001 a A0060000+, único | No | Generado por seed_database.py | - |
| patient_id | TEXT | Debe existir en tabla patients (FK) | No | Generado por seed_database.py | D1 (FK huérfana) |
| clinic_code | TEXT | """ + ", ".join(CLINIC_CODES) + """ | No | Generado por seed_database.py | D6 (formato alterado) |
| specialty | TEXT | """ + ", ".join(SPECIALTIES) + """ o alias válidos | Sí (1.5% de D3) | Generado por seed_database.py | D3 (NULL), D5 (nomenclatura) |
| scheduled_at | TEXT (YYYY-MM-DD HH:MM:SS) | 2024-01-01 a 2025-11-30, 08:00-18:45 | No | Generado por seed_database.py | D6 (formato alterado), D7 (anterior a registered_at) |
| duration_min | INTEGER | 15, 20, 30, 45, 60 | No | Generado por seed_database.py | D7 (0 con amount>0) |
| status | TEXT | 'completada', 'no_show', 'cancelada' | No | Generado por seed_database.py | - |
| amount_charged | REAL | > 0 (normalmente) | Sí (1.5% de D3) | Calculado | D2 (negativo/999999), D3 (NULL) |
| payment_method | TEXT | 'efectivo', 'tarjeta', 'transferencia', 'aseguradora' | No | Generado por seed_database.py | - |
| created_at | TEXT (YYYY-MM-DD HH:MM:SS) | scheduled_at menos 1-45 días | No | Generado por seed_database.py | - |

## Fuente 2: CSV - `tarifas_especialidad.csv`

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| clinic_code | TEXT | """ + ", ".join(CLINIC_CODES) + """ | No | Generado por seed_database.py | - |
| specialty | TEXT | """ + ", ".join(SPECIALTIES) + """ | No | Generado por seed_database.py | - |
| tarifa_base | INTEGER | 450-2200, múltiplos de 50 | No | Generado por seed_database.py | - |
| moneda | TEXT | Siempre 'MXN' | No | Generado por seed_database.py | - |
| vigencia_desde | TEXT (YYYY-MM-DD) | '2024-01-01' (80%) o '2025-01-01' (20%) | No | Generado por seed_database.py | - |

## Fuente 3: JSON - `catalogo_clinicas.json`

### Sección: clinicas

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| clinic_code | TEXT | """ + ", ".join(CLINIC_CODES) + """ | No | Definido en build_catalogo() | - |
| nombre | TEXT | Ver lista abajo | No | Definido en build_catalogo() | - |
| ciudad | TEXT | """ + ", ".join(CITIES[:4]) + """ | No | Definido en build_catalogo() | - |
| zona | TEXT | norte, sur, centro, este, oeste | No | Definido en build_catalogo() | - |
| aliases | ARRAY de TEXT | Mínimo 3 alias por clínica | No | Definido en build_catalogo() | - |

### Sección: especialidad_aliases

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| especialidad (key) | TEXT | """ + ", ".join(SPECIALTIES) + """ | No | Definido en build_catalogo() | - |
| aliases (value) | ARRAY de TEXT | Mínimo 2 alias por especialidad | No | Definido en build_catalogo() | - |

## Notas sobre los Defectos (D1-D7)

| ID | Defecto | Probabilidad | Descripción |
|----|---------|--------------|-------------|
| D1 | FK huérfana | 2.0% | patient_id no existe en tabla patients |
| D2 | Monto inválido | 1.0% | amount_charged negativo o 999999.0 |
| D3 | Nulo relevante | 3.0% | specialty o amount_charged = NULL |
| D4 | Duplicados | 2.0% | Filas duplicadas (exactas o casi-duplicadas) |
| D5 | Nomenclatura | 5.0% | specialty con alias (mayúsculas, sin acento, con espacios) |
| D6 | Defecto silencioso | 4.0% | clinic_code con comillas y espacios, o scheduled_at en otro formato |
| D7 | Regla física imposible | 0.5% | duration_min = 0 con amount_charged > 0, o scheduled_at < registered_at |

## Especialidades y sus Aliases (D5)

"""
    
    # Añadir tabla de aliases de especialidades
    md_content += "| Especialidad | Aliases |\n"
    md_content += "|--------------|---------|\n"
    
    # Cargar catálogo para obtener aliases reales
    catalogo_path = PATHS['catalogo']
    if catalogo_path.exists():
        with open(catalogo_path, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
            aliases = catalogo.get('especialidad_aliases', {})
            for specialty, alias_list in aliases.items():
                alias_str = ", ".join(alias_list)
                md_content += f"| {specialty} | {alias_str} |\n"
    else:
        md_content += "| *generado al ejecutar* | *ver archivo catalogo_clinicas.json* |\n"
    
    # Añadir información de clínicas
    md_content += """
## Clínicas y sus Aliases

| Clínica | Código | Ciudad | Zona | Aliases |
|---------|--------|--------|------|---------|
"""
    
    if catalogo_path.exists():
        with open(catalogo_path, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
            for clinica in catalogo.get('clinicas', []):
                alias_str = ", ".join(clinica.get('aliases', []))
                md_content += f"| {clinica['nombre']} | {clinica['clinic_code']} | {clinica['ciudad']} | {clinica['zona']} | {alias_str} |\n"
    else:
        md_content += "| *generado al ejecutar* | *ver archivo catalogo_clinicas.json* |\n"
    
    # Añadir distribuciones de probabilidad
    md_content += """
## Distribuciones de Probabilidad

### Sexo (patients)
- F: 54%
- M: 46%

### Ciudad (patients)
- Monterrey: 28%
- Guadalajara: 22%
- CDMX: 18%
- Puebla: 14%
- Tijuana: 11%
- Cancún: 7%

### Seguro (patients)
- ninguno: 45%
- basico: 40%
- premium: 15%

### Clínica (appointments)
- CL01: 30%
- CL02: 25%
- CL03: 20%
- CL04: 15%
- CL05: 10%

### Estado (appointments)
- completada: 78%
- no_show: 13%
- cancelada: 9%

### Método de Pago (appointments)
- efectivo: 30%
- tarjeta: 35%
- transferencia: 15%
- aseguradora: 20%

### Duración (appointments)
- 15 min: 30%
- 20 min: 25%
- 30 min: 25%
- 45 min: 15%
- 60 min: 5%
"""
    
    # Guardar el archivo en DOCS_DIR
    md_path = DOCS_DIR / "data_dictionary.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"   Diccionario de datos generado en {md_path}")
    return md_path

def main():
    print(f"Generando datos con seed: {SEED}")
    print(f"Pacientes: {N_PATIENTS}, Citas: {N_APPOINTMENTS}")
    print("-" * 50)
    
    # Construir catálogo
    print("1. Construyendo catálogo...")
    catalogo = build_catalogo()
    
    # Construir tarifas
    print("2. Construyendo tarifas...")
    tarifas = build_tarifas()
    
    # Construir pacientes
    print("3. Construyendo pacientes...")
    patients = build_patients()
    print(f"   {len(patients)} pacientes generados")
    
    # Calcular pesos para pacientes
    print("4. Calculando pesos para distribución no uniforme...")
    weights = rng.lognormal(mean=0.0, sigma=1.1, size=len(patients))
    weights = weights / weights.sum()
    
    # Construir citas
    print("5. Construyendo citas...")
    appointments = build_appointments(patients, weights, tarifas)
    print(f"   {len(appointments)} citas generadas")
    
    # Inyectar defectos
    print("6. Inyectando defectos...")
    appointments = inject_defects(appointments, patients)
    print(f"   Defectos inyectados: {sum(defect_counts.values())}")
    
    # Crear base de datos
    print("7. Creando base de datos...")
    create_database(patients, appointments)
    
    # Crear perfil
    print("8. Creando perfil de datos...")
    create_profile(patients, appointments)
    
    # Verificar checks
    verify_checks(patients, appointments)

    # Generar diccionario de datos
    print("9. Generando diccionario de datos...")
    generate_data_dictionary()
    
    print("\n" + "=" * 50)
    print("¡Generación completada exitosamente!")
    print(f"Archivos generados:")
    print(f"  - {PATHS['database']}")
    print(f"  - {PATHS['tarifas']}")
    print(f"  - {PATHS['catalogo']}")
    print(f"  - {PATHS['profile']}")
    print(f"  - {DOCS_DIR / 'data_dictionary.md'}")


if __name__ == "__main__":
    main()