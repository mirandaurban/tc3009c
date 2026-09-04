# Diccionario de Datos - Sistema de Citas Médicas

## Fuente 1: SQLite - Tabla `patients` (clinica.db)

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| patient_id | TEXT | Formato P000001 a P008000, único | No | Generado por seed_database.py | - |
| birth_date | TEXT (YYYY-MM-DD) | 1940-01-01 a 2015-12-31 | No | Generado por seed_database.py | - |
| sex | TEXT | 'F' o 'M' | No | Generado por seed_database.py | - |
| city | TEXT | Monterrey, Guadalajara, CDMX, Puebla, Tijuana, Cancún | No | Generado por seed_database.py | - |
| insurance | TEXT | 'ninguno', 'basico', 'premium' | No | Generado por seed_database.py | - |
| registered_at | TEXT (YYYY-MM-DD) | 2022-01-01 a 2024-12-31 | No | Generado por seed_database.py | - |

## Fuente 1: SQLite - Tabla `appointments` (clinica.db)

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| appointment_id | TEXT | Formato A0000001 a A0060000+, único | No | Generado por seed_database.py | - |
| patient_id | TEXT | Debe existir en tabla patients (FK) | No | Generado por seed_database.py | D1 (FK huérfana) |
| clinic_code | TEXT | CL01, CL02, CL03, CL04, CL05 | No | Generado por seed_database.py | D6 (formato alterado) |
| specialty | TEXT | Medicina General, Pediatría, Traumatología, Cardiología, Dermatología, Ginecología, Odontología, Oftalmología o alias válidos | Sí (1.5% de D3) | Generado por seed_database.py | D3 (NULL), D5 (nomenclatura) |
| scheduled_at | TEXT (YYYY-MM-DD HH:MM:SS) | 2024-01-01 a 2025-11-30, 08:00-18:45 | No | Generado por seed_database.py | D6 (formato alterado), D7 (anterior a registered_at) |
| duration_min | INTEGER | 15, 20, 30, 45, 60 | No | Generado por seed_database.py | D7 (0 con amount>0) |
| status | TEXT | 'completada', 'no_show', 'cancelada' | No | Generado por seed_database.py | - |
| amount_charged | REAL | > 0 (normalmente) | Sí (1.5% de D3) | Calculado | D2 (negativo/999999), D3 (NULL) |
| payment_method | TEXT | 'efectivo', 'tarjeta', 'transferencia', 'aseguradora' | No | Generado por seed_database.py | - |
| created_at | TEXT (YYYY-MM-DD HH:MM:SS) | scheduled_at menos 1-45 días | No | Generado por seed_database.py | - |

## Fuente 2: CSV - `tarifas_especialidad.csv`

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| clinic_code | TEXT | CL01, CL02, CL03, CL04, CL05 | No | Generado por seed_database.py | - |
| specialty | TEXT | Medicina General, Pediatría, Traumatología, Cardiología, Dermatología, Ginecología, Odontología, Oftalmología | No | Generado por seed_database.py | - |
| tarifa_base | INTEGER | 450-2200, múltiplos de 50 | No | Generado por seed_database.py | - |
| moneda | TEXT | Siempre 'MXN' | No | Generado por seed_database.py | - |
| vigencia_desde | TEXT (YYYY-MM-DD) | '2024-01-01' (80%) o '2025-01-01' (20%) | No | Generado por seed_database.py | - |

## Fuente 3: JSON - `catalogo_clinicas.json`

### Sección: clinicas

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| clinic_code | TEXT | CL01, CL02, CL03, CL04, CL05 | No | Definido en build_catalogo() | - |
| nombre | TEXT | Ver lista abajo | No | Definido en build_catalogo() | - |
| ciudad | TEXT | Monterrey, Guadalajara, CDMX, Puebla | No | Definido en build_catalogo() | - |
| zona | TEXT | norte, sur, centro, este, oeste | No | Definido en build_catalogo() | - |
| aliases | ARRAY de TEXT | Mínimo 3 alias por clínica | No | Definido en build_catalogo() | - |

### Sección: especialidad_aliases

| Columna | Tipo | Dominio Válido | Nulos Permitidos | Origen | Defectos Posibles |
|---------|------|----------------|------------------|--------|-------------------|
| especialidad (key) | TEXT | Medicina General, Pediatría, Traumatología, Cardiología, Dermatología, Ginecología, Odontología, Oftalmología | No | Definido en build_catalogo() | - |
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

| Especialidad | Aliases |
|--------------|---------|
| Medicina General | med gral, MEDICINA_GENERAL, medicina general , MG, med-general |
| Pediatría | pediatria, PEDIATRIA, pediatría, PED, ped |
| Traumatología | traumatologia, TRAUMA, Traumatología, TRA, trauma |
| Cardiología | cardiologia, CARDIOLOGIA, Cardiología, CAR, cardio |
| Dermatología | dermatologia, DERMATOLOGIA, Dermatología, DER, derma |
| Ginecología | ginecologia, GINECOLOGIA, Ginecología, GIN, gineco |
| Odontología | odontologia, ODONTOLOGIA, Odontología, ODO, odonto |
| Oftalmología | oftalmologia, OFTALMOLOGIA, Oftalmología, OFT, oftalmo |

## Clínicas y sus Aliases

| Clínica | Código | Ciudad | Zona | Aliases |
|---------|--------|--------|------|---------|
| SaludNorte Centro | CL01 | Monterrey | norte | CL-01, cl01, Clinica Centro, SaludNorte, SN01 |
| Hospital Sur | CL02 | Guadalajara | sur | CL-02, cl02, Hospital del Sur, HS02, Clinica Sur |
| Centro Médico Central | CL03 | CDMX | centro | CL-03, cl03, CMC, Central, Clinica Central |
| Clínica del Este | CL04 | Puebla | este | CL-04, cl04, Este, Clinica Este, CE04 |
| Salud del Oeste | CL05 | Tijuana | oeste | CL-05, cl05, Oeste, Clinica Oeste, SO05 |

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
