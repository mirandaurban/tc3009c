# Examen Parcial — De Laboratorio a Pipeline de Datos Productivo

**TC3009C.602 — Miranda Urban Solano A01752391**

---

## Caso del examen

**Red de clínicas "SaludNorte".** Operan 5 sucursales y 8 especialidades.
El área de operación necesita una tabla curada de citas médicas para medir
ingreso real por especialidad y sucursal, y la tasa de inasistencia
(_no-show_). Hoy no puede: la información de pacientes y citas vive en una base
operativa, las tarifas llegan en un CSV que mantiene Finanzas a mano, y el
catálogo de sucursales viene en un JSON con nombres escritos de varias formas.

Objetivo del pipeline: producir la tabla `appointments_curated`, más
`appointments_rejects` y `etl_runs`.

### Análisis de objetivos producidos

De acuerdo al análisis realizado, la tabla curada es sumamente importante para la decisión de negocio debido a que sirve como una referencia clave al área de operación, pues permite identificar qué especialidades generan mayor ingreso real y qué sucursales presentan tasas de ausencias superiores al promedio, factores clave para la asignación de recursos, estrategias de retención de pacientes y ajustes en la gestión de citas. En pocas palabras, los resultados del pipeline permiten la identificación de problemas puntuales y urgentes facilitando la toma de decisiones con base en datos confiables, estructurados y relevantes para la operación.

---

## Estructura del Proyecto

```bash
Examen/
├── README.md
├── config.json                        # Configuración del pipeline
│
├── data/                              # DIRECTORIO DE DATOS
│   ├── benchmark_results.json         # Resultados del benchmark Pandas vs Spark (tiempos por volumen)
│   ├── benchmark_results.png          # Gráfica comparativa de tiempos de ejecución
│   ├── catalogo_clinicas.json         # Catálogo de clínicas y aliases para homologación
│   ├── clinica.db                     # Base de datos origen (operativa)
│   ├── clinica_curated.db             # Base de datos destino (curada)
│   ├── data_profile.json              # Perfil de datos generados
│   ├── etl.log                        # Log de ejecución del pipeline
│   ├── tarifas_especialidad.csv       # Tarifas base por clínica y especialidad
│   ├── watermark.json                 # Watermark para procesamiento incremental
│   │
│   ├── volume_1M/                     # Datos para benchmark: 1M registros
│   │   ├── clinica_curated.db
│   │   └── fact_appointments.csv
│   ├── volume_250k/                   # Datos para benchmark: 250K registros
│   │   ├── clinica_curated.db
│   │   └── fact_appointments.csv
│   ├── volume_4M/                     # Datos para benchmark: 4M registros
│   │   ├── clinica_curated.db
│   │   └── fact_appointments.csv
│   └── volume_60k/                    # Datos para benchmark: 60K registros
│       ├── clinica_curated.db
│       └── fact_appointments.csv
│
├── docs/                              # DOCUMENTACIÓN
│   ├── data_dictionary.md             # Diccionario de datos de todas las fuentes
│   ├── resultados_consultas.json      # Resultados de consultas analíticas (formato JSON)
│   ├── resultados_consultas.md        # Resultados de consultas analíticas (formato Markdown)
│   └── runbook.md                     # Runbook de operación del pipeline
│
├── notebooks/
│   └── 01_exploracion.ipynb
│
├── scripts/                           # SRIPTS AUXILIARES
│   └── seed_database.py               # Generador de datos sintéticos
│
├── sql/                               # CONSULTAS SQL
│   └── consultas.sql                  # Consultas analíticas sobre la tabla curada
│
├── src/                               # CÓDIGO FUENTE
│   ├── append_new_batch.py            # Genera nuevo lote de citas
│   ├── benchmark_spark.py             # Benchmark de escalabilidad Pandas vs Spark
│   ├── contracts.py                   # Contratos de datos y validaciones
│   ├── etl.py                         # Pipeline ETL
│   ├── generate_data_volumes.py       # Generador de volúmenes para benchmark
│   ├── run_queries.py                 # Ejecuta consultas SQL y guarda resultados
│   └── verify_etl.py                  # Verificador de resultados del ETL
│
├── tests/                             # PRUEBAS
│   ├── conftest.py                    # Fixtures para pruebas
│   ├── test_contracts.py              # Pruebas de contratos de datos (8 pruebas)
│   └── test_etl.py                    # Pruebas del pipeline ETL (7 pruebas)
│
├── requirements.txt                   # Dependencias del proyecto
└── run_all.sh
```

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd Examen

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Ejecución del proyecto

### Generar datos de prueba

```bash
python scripts/seed_database.py
```

### Ejecutar ETL completo

```bash
python src/etl.py
```

### Verificar resultados

```bash
python scripts/verify_etl.py
```

### Agregar nuevo lote de citas (prueba incremental)

```bash
python scripts/append_new_batch.py
python src/etl.py  # Solo procesa las nuevas
```

### Ejecutar consultas analíticas

```bash
python src/run_queries.py
```

### Ejecutar pruebas

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

---

## Pipeline ETL

El pipeline sigue el flujo:

| Etapa            | Descripción                                                                                                                         |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **DEFINE**       | Configuración del pipeline desde `config.json`                                                                                      |
| **EXTRACT**      | Extracción incremental de citas                                                                                                     |
| **STAGE**        | Adición de metadatos de origen                                                                                                      |
| **VALIDATE**     | Validación contra contratos y separación de datos: registros válidos siguen el proceso y registros inválidos van cuarentena         |
| **TRANSFORM**    | Homologación, limpieza y derivación de variables                                                                                    |
| **INTEGRATE**    | Join de pacientes, citas y tarifas                                                                                                  |
| **QUALITY GATE** | Verificación de umbrales de calidad: detiene la carga de datos si falla o continúa si estos cumplen con los parámetros determinados |
| **LOAD**         | UPSERT idempotente en `fact_appointments`                                                                                           |
| **AUDIT**        | Registro de ejecución en `etl_runs` para temas de trazabilidad y auditoría                                                          |

### Variables derivadas

| Variable               | Descripción                                       |
| ---------------------- | ------------------------------------------------- |
| `patient_age_at_visit` | Edad del paciente al momento de la cita           |
| `is_no_show`           | 1 si la cita fue no-show, 0 en otro caso          |
| `revenue_gap`          | Diferencia entre `amount_charged` y `tarifa_base` |
| `is_peak_hour`         | 1 si la cita es entre 9:00 y 13:00                |
| `scheduled_hour`       | Hora de la cita (0-23)                            |
| `duration_hours`       | Duración en horas                                 |

### Defectos detectados y su tratamiento (D1-D7)

| ID  | Defecto            | Tratamiento                                                    | Justificación                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --- | ------------------ | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | FK huérfana        | Rechazo: `patient_id_fk_missing`                               | De acuerdo a las reglas de negocio, no se puede realizar una cita sin paciente válido. Por lo que la existencia de este tipo de defecto sugiere que dicha información no es confiable y que el registrp debe ser rechazado para evitar sesgos en métricas como ingreso por paciente o tasa de no-show.                                                                                                                                                                                        |
| D2  | Monto inválido     | Rechazo: `amount_charged_negative`, `amount_charged_sentinel`  | La forma en que se calculan los montos para el negocio no debe permitir montos negativos o excesivamente grandes (anomalías fuera de los rangos normales), por lo que la aparición de registros de este tipo son un error evidente. Su presencia puede distorcionar el análisis del ingreso total, por lo que deben rechazarse para no contaminar los indicadores financieros.                                                                                                                |
| D3  | Nulo relevante     | Rechazo: `specialty_null`, `amount_charged_null`               | Si la especialidad tiene como valor `null`, la cita no puede clasificarse correctamente. El monto cobrado es necesario para calcular ingreso y ticket promedio. Ambos campos son esenciales para los análisis de negocio, por lo que son imprescindibles para poder realizar el análisis.                                                                                                                                                                                                     |
| D4  | Duplicados         | Deduplicación exactos y casi-duplicados                        | Los duplicados inflan artificialmente el conteo de citas y el ingreso total, por lo que deben de ser tratados. Los duplicados exactos por ID se resuelven por UPSERT. Los casi-duplicados (mismo paciente, clínica, especialidad, fecha y duración) se detectan y eliminan para evitar doble conteo.                                                                                                                                                                                          |
| D5  | Nomenclatura       | Homologación con `catalogo_clinicas.json`                      | Los alias de especialidades son variaciones del mismo concepto. No deben de rechazarse porque representan información valiosa para el análisis, es por ello que se normalizan al valor canónico para mantener consistencia en los análisis sin perdercdatos. Dentro de un sistema de este tipo, sería ideal resolver el problema desde la raíz (formulario de citas, etc.), pero siempre resulta valioso tener un enfoque como este dado que es un problema común es este tipo de soluciones. |
| D6  | Defecto silencioso | Normalización: fechas formato mixto, limpieza de strings       | Existen diferentes formatos de fechas (pero que al final transmiten la misma información, cuando ocurrió un evento) o códigos con errores de formato, no de contenido. Con el fin de sacar provecho de estos registros, en vez de eliminarlos, se normalizan para poder procesarlos correctamente.                                                                                                                                                                                            |
| D7  | Regla imposible    | Rechazo: `scheduled_before_registered`, `duration_min_invalid` | Una cita agendada antes del registro del paciente rompe la lógica de negocio, ya que no es posible agendar a un paciente que aún no existe en el sistema. Al igual que duración 0 con cobro positivo es físicamente imposible, ya que se debe de acudir a la cita para poder realizar el cobro. Ambos casos se rechazan por violar reglas de negocio fundamentales.                                                                                                                           |

---

## Análisis de Resultados de Consultas Analíticas

### 1. Ingreso total y ticket promedio por especialidad

**Datos actualizados:**

| Especialidad     | Total Citas | Ingreso Total | Ticket Promedio | Ticket promedio en Centenas |
| ---------------- | ----------- | ------------- | --------------- | --------------------------- |
| Dermatología     | 8,256       | $9,214,925.04 | $1,116.15       | 11.16                       |
| Traumatología    | 10,193      | $8,926,343.44 | $875.73         | 8.76                        |
| Medicina General | 7,513       | $7,900,323.55 | $1,051.55       | 10.52                       |
| Ginecología      | 5,613       | $6,435,771.03 | $1,146.58       | 11.47                       |
| Odontología      | 5,865       | $6,159,049.89 | $1,050.14       | 10.50                       |
| Oftalmología     | 2,891       | $3,916,854.03 | $1,354.84       | 13.55                       |
| Cardiología      | 2,814       | $3,382,293.87 | $1,201.95       | 12.02                       |
| Pediatría        | 3,301       | $2,485,101.51 | $752.83         | 7.53                        |
| Sin especificar  | 703         | $759,013.84   | $1,079.68       | 10.80                       |

**Interpretación:** Dermatología es la especialidad que genera el mayor ingreso total ($9.2M), seguida de Traumatología ($8.9M). Sin embargo, Oftalmología tiene el ticket promedio más alto ($1,354.84), lo que indica que aunque tiene menos volumen (2,891 citas), es un servicio de alta complejidad y alto valor. En contraste, Pediatría tiene el ticket promedio más bajo ($752.83) y un volumen medio (3,301 citas), lo que sugiere que es un servicio de alta rotación pero bajo margen. Las 703 citas sin especialidad representan un área de oportunidad para mejorar la captura de datos en el origen.

Sí, la información coincide con la interpretación. Sin embargo, hay una ligera mejora en la redacción. Aquí está la versión corregida:

---

### 2. Tasa de no-show por sucursal (superan promedio)

| Sucursal | Total Citas | No-Show | Tasa   | Promedio General | Diferencia |
| -------- | ----------- | ------- | ------ | ---------------- | ---------- |
| CL05     | 5,336       | 749     | 14.04% | 12.89%           | +1.15%     |
| CL03     | 10,395      | 1,383   | 13.30% | 12.89%           | +0.41%     |

**Interpretación:** CL05 presenta la tasa de no-show más alta (14.04%), superando el promedio general en 1.15 puntos porcentuales. Esto puede indicar problemas de accesibilidad, falta de recordatorios efectivos o sobre-agendamiento en esta sucursal. CL03, a pesar de tener el mayor volumen de citas (10,395), también supera el promedio general (13.30% vs 12.89%). Se recomienda implementar estrategias de recordatorio (SMS, recordatorios telefónicos) en CL05 como medida prioritaria y monitorear la evolución de CL03. El resto de las sucursales se encuentran por debajo del promedio, lo que sugiere que el problema está focalizado en estas dos ubicaciones.

### 3. Ingreso mensual por sucursal y variación

| Sucursal | Mejor mes | Ingreso pico | Nov 2025 | Variación Nov | Tendencia   |
| -------- | --------- | ------------ | -------- | ------------- | ----------- |
| CL01     | 2025-10   | $795,320     | $653,970 | -17.77%       | Disminución |
| CL02     | 2025-10   | $627,882     | $534,970 | -14.80%       | Disminución |
| CL03     | 2025-08   | $554,214     | $449,091 | -15.65%       | Disminución |
| CL04     | 2025-07   | $311,212     | $250,991 | -17.51%       | Disminución |
| CL05     | 2025-10   | $275,018     | $214,406 | -22.04%       | Disminución |

**Interpretación**: Todas las sucursales presentan una caída consistente en noviembre 2025 (-14.8% a -22%), indicando un fenómeno estacional pre-navideño. CL01 es la sucursal con mayor ingreso absoluto y crecimiento sostenido (+323% desde enero 2024). CL05 destaca por su alta volatilidad, con una caída del -22% en noviembre tras un crecimiento del +38% en octubre. Se recomienda investigar las causas de la caída generalizada y diseñar estrategias de retención para CL03 y CL05.

### 4. Top 10 de pacientes por número de citas y revenue_gap acumulado

| Paciente | Citas | Total Gastado | Ticket Promedio | Revenue Gap | Gap por Cita | Edad | Clasificación  |
| -------- | ----- | ------------- | --------------- | ----------- | ------------ | ---- | -------------- |
| P002156  | 161   | $135,981      | $844.60         | -$58,089    | -$363.06     | 55   | Descuento alto |
| P001525  | 153   | $135,257      | $884.03         | -$50,883    | -$339.22     | 20   | Descuento alto |
| P002973  | 150   | $132,539      | $883.59         | -$48,211    | -$321.41     | 77   | Descuento alto |
| P003269  | 139   | $135,004      | $971.25         | -$32,070    | -$234.09     | 19   | Descuento alto |
| P000196  | 125   | $113,681      | $909.45         | -$37,430    | -$301.85     | 38   | Descuento alto |
| P002554  | 122   | $120,113      | $984.54         | -$36,987    | -$303.17     | 57   | Descuento alto |
| P005980  | 119   | $124,683      | $1,047.76       | -$24,010    | -$206.98     | 55   | Descuento alto |
| P004271  | 114   | $100,948      | $885.51         | -$36,807    | -$328.63     | 41   | Descuento alto |
| P002388  | 108   | $106,170      | $983.06         | -$25,084    | -$238.90     | 55   | Descuento alto |
| P002527  | 107   | $105,112      | $982.35         | -$25,129    | -$246.37     | 53   | Descuento alto |

**Interpretación:** Los 10 pacientes más frecuentes (107-161 citas) acumulan entre $24,000 y $58,000 en revenue_gap negativo, con descuentos promedio de $207 a $363 por cita. Todos los pacientes presentan clasificación de "Descuento alto", lo que sugiere que los pacientes más leales son también los que reciben mayores descuentos. Se recomienda revisar las políticas de descuento para pacientes frecuentes y validar los convenios con aseguradoras para confirmar que este modelo es conveniente para el negocio.

### 5. Distribución de motivos de rechazo por mes

**Datos actualizados (septiembre 2026):**

| Motivo de rechazo           | Cantidad | Total rechazos | Porcentaje |
| --------------------------- | -------- | -------------- | ---------- |
| scheduled_before_registered | 13,503   | 24,290         | 55.59%     |
| duration_min_invalid        | 5,426    | 24,290         | 22.34%     |
| patient_id_fk_missing       | 3,450    | 24,290         | 14.20%     |
| amount_charged_sentinel     | 843      | 24,290         | 3.47%      |
| amount_charged_negative     | 678      | 24,290         | 2.79%      |
| scheduled_before_created    | 390      | 24,290         | 1.61%      |

**Interpretación actualizada:** El principal motivo de rechazo es `scheduled_before_registered` (55.59%), lo que indica un problema sistémico en el proceso de agendamiento: las citas se crean antes de que el paciente esté registrado en el sistema. Esto requiere una intervención inmediata en el flujo de registro de pacientes. El segundo motivo más frecuente es `duration_min_invalid` (22.34%), lo que sugiere que muchas citas tienen duraciones que no corresponden a los valores válidos (15, 20, 30, 45, 60 minutos). `patient_id_fk_missing` (14.20%) indica que hay citas asociadas a pacientes que no existen en la tabla de pacientes, posiblemente por errores en la integración entre sistemas. Los demás motivos representan menos del 10% combinado. Se recomienda priorizar la corrección del proceso de agendamiento para eliminar la causa raíz del 55.59% de los rechazos.

---

## Análisis de Benchmark de Escalabilidad (Pandas vs Spark)

### Resultados actualizados

| Volumen | Pandas (mediana) | PySpark (mediana) | Ratio (Pandas/Spark) |
| ------- | ---------------- | ----------------- | -------------------- |
| 60K     | 0.19s            | 0.42s             | 0.45x                |
| 250K    | 0.75s            | 0.39s             | 1.92x                |
| 1M      | 3.02s            | 0.60s             | 5.03x                |
| 4M      | 12.19s           | 1.76s             | 6.93x                |

### Overhead de Spark

El overhead de arranque de Spark medido es de **0.55s** (significativamente menor que los 2.1s estimados anteriormente). Esto cambia el análisis del punto de inflexión.

### Análisis del punto de inflexión

| Volumen | Pandas | Spark | Ganador                  |
| ------- | ------ | ----- | ------------------------ |
| 60K     | 0.19s  | 0.42s | Pandas (2.2x más rápido) |
| 250K    | 0.75s  | 0.39s | Spark (1.9x más rápido)  |
| 1M      | 3.02s  | 0.60s | Spark (5.0x más rápido)  |
| 4M      | 12.19s | 1.76s | Spark (6.9x más rápido)  |

**Punto de inflexión:** El punto de inflexión se encuentra entre 60K y 250K registros. Para volúmenes menores a ~150K, Pandas es más rápido. Para volúmenes superiores, Spark es más eficiente.

### Recomendación actualizada

Para el volumen actual de producción (~60K registros), Pandas es 2.2 veces más rápido que Spark, y el overhead de arranque de Spark (0.55s) no se justifica. Sin embargo, si el volumen de datos crece por encima de 250K registros, Spark se vuelve más eficiente (1.9x más rápido en 250K, 5x en 1M, 7x en 4M). Se recomienda mantener Pandas para el volumen actual y migrar a Spark solo si el volumen de datos supera consistentemente los 250K registros. La ganancia de Spark se vuelve significativa en volúmenes superiores a 1M, donde es 5 veces más rápido que Pandas.

## Pruebas

### Cobertura

```
tests/
├── test_contracts.py (8 pruebas)
│   ├── test_patient_id_regex
│   ├── test_appointment_id_regex
│   ├── test_valid_specialties
│   ├── test_valid_clinic_codes
│   ├── test_patients_contract_structure
│   ├── test_appointments_contract_structure
│   ├── test_tarifas_contract_structure
│   └── test_column_nullability
└── test_etl.py (7 pruebas)
    ├── test_patient_age_at_visit
    ├── test_negative_amount_rejected
    ├── test_quality_gate_threshold
    ├── test_idempotency
    ├── test_homologacion_specialty
    ├── test_homologacion_clinic_code
    └── test_revenue_gap_calculation
```

### Ejecutar pruebas

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

### Resultados esperados

```
tests/test_contracts.py ........
tests/test_etl.py .......
==================================== 15 passed in 0.05s ====================================
```

---

## Operación

### Ejecución programada

**Linux / MacOS (Cron):**

```bash
# Editar crontab
crontab -e

# Ejecución diaria a las 2:00 AM
0 2 * * * cd /ruta/al/proyecto && source .venv/bin/activate && python src/etl.py >> data/cron.log 2>&1
```

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "ETL_Citas_Medicas" /tr "C:\ruta\al\proyecto\.venv\Scripts\python.exe C:\ruta\al\proyecto\src\etl.py" /sc daily /st 02:00
```

### Monitoreo

```bash
# Verificar última ejecución
python scripts/verify_etl.py

# Revisar logs
tail -100 data/etl.log
```

---

## Información generada a partir de automatizaciones

Con el fin de eficientar las tareas de análisis, parte de las evidencias se generan automáticamente con código. Esto con el fin de que el tiempo invertido en esta sección se centre precisamente en el análisis, no en la generación de la información en la que este se basa.

En el caso del diccionario de datos, la información sobre los datos se crea al momento de la generación de datos con el fin de que la información reportada sea consistente con la que se ha producido. Se puede ver en:

- [Diccionario de Datos](docs/data_dictionary.md)

Para confirmar que el funcionamiento de `append_new_batch.py` fuera correcto, se obtuvieron los hash de estos procesos. Los resultados pueden observarse en los siguientes archivos donde se aprecia que el hash es el mismo (a excepción del perfil porque este cambia en cada iteración):

- [Hash de ejecución 1](tests/evidencia_hash/hash1.txt)
- [Hash de ejecución 2](tests/evidencia_hash/hash2.txt)

Al ejecutar el archivo de `src/run_queries.py` se genera de forma automática un reporte (en JSON y Markdown) con las evidencias obtenidas, paso fundamental para el análisis realizado en la sección de _Análisis de Resultados de Consultas Analíticas_. Véase los archivos para un mejor entendimiento de esa sección:

- [JSON de resultados de consultas](docs/resultados_consultas.json)
- [Markdown de resultados de consultas](docs/resultados_consultas.md)

En el caso del benchmark, al ejecutar el código, los resultados de este proceso se generan y guardan automáticamente. Los resultados obtenidos se pueden ver en:

- [JSON de resultados del benchmark](data/benchmark_results.json)
- [Gráfico de los resultados del benchmark](data/benchmark_results.png)

Extra: La ejecución de prueba realizada para la demostración del examen puede verse en el siguiente archivo:

- [Evidencia terminal](docs/evidencia_terminal.txt)

---

## Documentación Adicional

- [Diccionario de Datos](docs/data_dictionary.md)
- [Runbook de Operación](docs/runbook.md)
- [Consultas SQL](data/resultados_consultas.sql)

## Declaración de uso de IA

**Se utilizó IA**

- **Herramienta:** Claude (Anthropic)
- **Uso realizado:** Apoyo durante el desarrollo y revisión de código, principalmente para explorar alternativas de implementación, resolver dudas puntuales y realizar ajustes conforme a las especificaciones del proyecto.
- **Secciones donde se utilizó:** Implementación y ajustes del código correspondiente a la funcionalidad desarrollada.
- **Validación realizada por el estudiante:** El código fue revisado, guiado y modificado durante el proceso de desarrollo para asegurar su correspondencia con las especificaciones y requerimientos establecidos.
- **Otro (especifique):** La herramienta se utilizó como apoyo al proceso de programación; las decisiones de implementación, modificaciones y validación final fueron realizadas por el estudiante.
