# Runbook

## Resumen

Este documento describe la operación del pipeline ETL para el sistema de citas medicas. Procesa datos de pacientes, citas y tarifas, aplicando reglas de calidad y generando una base de datos curada.

El pipeline sigue el flujo:

```
DEFINE → EXTRACT → STAGE → VALIDATE → TRANSFORM → INTEGRATE → QUALITY GATE → LOAD → AUDIT
```

## Como correrlo

### Ejecución manual

```bash
cd /ruta/al/proyecto
source .venv/bin/activate
python src/etl.py
```

### Ejecución con datos especificos

```bash
# Generar datos de prueba
python scripts/seed_database.py

# Ejecutar ETL
python src/etl.py

# Verificar resultados
python scripts/verify_etl.py
```

### Ejecución incremental

El pipeline usa watermark por `created_at`. Por lo que las ejecuciones consecuentes

```bash
# Primera ejecución
python src/etl.py

# Agregar nuevos datos
python scripts/append_new_batch.py

# Segunda ejecución (solo datos nuevos)
python src/etl.py
```

## Como saber si fallo

### 1. Revisar logs

```bash
tail -100 data/etl.log
```

Se debe de buscar etiquetas como:

- `ERROR` - fallo critico
- `WARNING` - problemas no criticos
- `FAILED_QUALITY_GATE` - calidad insuficiente

### 2. Revisar tabla de auditoria

```bash
sqlite3 data/clinica_curated.db
SELECT * FROM etl_runs ORDER BY started_at DESC LIMIT 1;
```

Campos clave para revisión:

- `status`: SUCCESS / FAIL / SUCCESS_EMPTY / FAILED_QUALITY_GATE
- `quality_status`: PASS / FAIL
- `error_message`: descripcion del error

### 3. Verificar cuarentena

```bash
sqlite3 data/clinica_curated.db
SELECT
    source,
    reject_reason,
    COUNT(*) as cantidad
FROM quarantine
GROUP BY source, reject_reason
ORDER BY cantidad DESC;
```

### 4. Verificar integridad de datos

```bash
sqlite3 data/clinica_curated.db
SELECT
    COUNT(*) as total_citas,
    COUNT(DISTINCT patient_id) as pacientes_unicos,
    SUM(amount_charged_clean) as ingreso_total,
    ROUND(AVG(amount_charged_clean), 2) as ticket_promedio
FROM fact_appointments;
```

## Instrucciones a seguir si el quality gate se dispara

El quality gate falla cuando se superan los umbrales definidos en `config.json`:

| Metrica                  | Umbral | Descripcion               |
| ------------------------ | ------ | ------------------------- |
| `unmatched_tarifa_rate`  | > 15%  | Citas sin tarifa asociada |
| `unmatched_patient_rate` | > 15%  | Citas sin paciente valido |
| `reject_rate`            | > 30%  | Tasa de rechazo global    |
| `duplicate_rate`         | > 10%  | Citas duplicadas          |
| `completeness`           | < 70%  | Datos incompletos         |

### Acciones correctivas

**1. Identificar la causa raiz**

```bash
# Ver razones de rechazo mas comunes
sqlite3 data/clinica_curated.db
SELECT reject_reason, COUNT(*) as cantidad
FROM quarantine
WHERE source = 'appointments'
GROUP BY reject_reason
ORDER BY cantidad DESC
LIMIT 10;
```

**2. Causas comunes y soluciones**

| Problema                      | Causa                                           | Solucion                                                |
| ----------------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| `unmatched_tarifa_rate` alto  | Especialidades o clinicas sin tarifa            | Revisar y agregar tarifas en `tarifas_especialidad.csv` |
| `unmatched_patient_rate` alto | Pacientes sin registro en tabla patients        | Verificar integridad de datos origen                    |
| `reject_rate` alto            | Multiples problemas de calidad                  | Revisar logs y corregir datos origen                    |
| `duplicate_rate` alto         | Duplicados en datos origen                      | Ejecutar deduplicacion manual                           |
| `scheduled_before_registered` | Citas agendadas antes del registro del paciente | Revisar procesos de registro                            |
| `amount_charged_negative`     | Montos negativos en datos origen                | Validar ingreso de montos                               |

**3. Ajustar umbrales (solución temporal)**

Si los umbrales son demasiado estrictos para datos de prueba, ajustar en `config.json`:

```json
"quality_thresholds": {
    "completeness_min": 0.60,
    "duplicate_rate_max": 0.15,
    "null_foreign_key_max": 0.20,
    "invalid_amount_max": 0.20,
    "max_rule_violation_pct": 0.70
}
```

**4. Reprocesar con umbrales ajustados**

```bash
python src/etl.py
```

**5. Escalar a nivel 2 si el problema persiste**

## Como reprocesar un dia

### Reprocesamiento completo

```bash
# 1. Resetear watermark al inicio del rango de datos
echo '{"last_processed_at": "2024-01-01 00:00:00"}' > data/watermark.json

# 2. Eliminar datos curados (opcional, si se requiere empezar desde cero)
rm -f data/clinica_curated.db

# 3. Reconstruir base de datos
python src/etl.py
```

### Reprocesamiento incremental desde una fecha especifica

```bash
# 1. Ver ultimo watermark
cat data/watermark.json

# 2. Ajustar watermark a fecha especifica
echo '{"last_processed_at": "2024-06-01 00:00:00"}' > data/watermark.json

# 3. Ejecutar ETL (procesara desde esa fecha en adelante)
python src/etl.py
```

### Reprocesar solo citas rechazadas

```bash
# 1. Exportar citas en cuarentena a CSV
sqlite3 data/clinica_curated.db <<EOF
.mode csv
.headers on
.output quarantine_citas.csv
SELECT * FROM quarantine WHERE source = 'appointments';
.output stdout
EOF

# 2. Corregir datos en archivo CSV (manualmente)

# 3. Cargar datos corregidos (necesita script personalizado)
```

## A quien escalar

### Nivel 1 - Operador

**Responsable**: Equipo de operaciones / Soporte

**Cuando contactar**:

- El pipeline falla por problemas de infraestructura
- Error de conexion a base de datos
- Tiempo de ejecución excesivo (> 30 minutos)
- Error de permisos o espacio en disco

**Acciones**:

1. Verificar disponibilidad de base de datos origen
2. Verificar espacio en disco: `df -h data/`
3. Verificar que el archivo `config.json` existe y es valido
4. Reintentar ejecución

**Informacion a recopilar**:

- Ultimas lineas de `data/etl.log`
- Estado de `etl_runs` en la base de datos
- Espacio disponible en disco

### Nivel 2 - Data Engineer

**Responsable**: Equipo de datos

**Cuando contactar**:

- Quality gate falla repetidamente
- Errores en transformaciones de datos
- Inconsistencias en datos curados
- Cambios en estructura de datos origen
- `unmatched_tarifa_rate` o `unmatched_patient_rate` persistentes

**Acciones**:

1. Revisar logs detallados
2. Validar contratos de datos (`contracts.py`)
3. Ajustar reglas de transformacion
4. Actualizar configuracion
5. Revisar integridad de datos origen

**Informacion a recopilar**:

- Log completo de la ejecución fallida
- Estado de cuarentena: `SELECT * FROM quarantine`
- Muestra de datos problema
- Ultimos cambios en datos origen o configuracion

### Nivel 3 - Data Architect / Developer

**Responsable**: Arquitecto de datos / Desarrollador senior

**Cuando contactar**:

- Cambios arquitectonicos necesarios
- Nuevas fuentes de datos
- Problemas de rendimiento persistentes
- Cambios en requerimientos de negocio
- Bugs en el codigo del pipeline

**Acciones**:

1. Revisar diseno del pipeline
2. Optimizar consultas y transformaciones
3. Actualizar contratos de datos
4. Corregir bugs en el codigo

**Informacion a recopilar**:

- Todo lo anterior
- Plan de ejecución de Spark (si aplica)
- Metricas de rendimiento
- Requerimientos de negocio actualizados

## Programacion (Cron / Task Scheduler)

### Linux / MacOS (Cron)

**Entrada conceptual**: Ejecución programada diaria a las 2:00 AM

**Comando**:

```bash
# Editar crontab
crontab -e

# Agregar linea para ejecución diaria a las 2:00 AM
0 2 * * * cd /ruta/al/proyecto && source .venv/bin/activate && python src/etl.py >> data/cron.log 2>&1

# Agregar linea para ejecución cada 4 horas (si se requiere mas frecuencia)
0 */4 * * * cd /ruta/al/proyecto && source .venv/bin/activate && python src/etl.py >> data/cron.log 2>&1
```

### Windows (Task Scheduler)

**Entrada conceptual**: Ejecución programada diaria a las 2:00 AM

**Comando**:

```powershell
# Crear tarea programada
schtasks /create /tn "ETL_Citas_Medicas" /tr "C:\ruta\al\proyecto\.venv\Scripts\python.exe C:\ruta\al\proyecto\src\etl.py" /sc daily /st 02:00

# Crear tarea con mas frecuencia (cada 4 horas)
schtasks /create /tn "ETL_Citas_Medicas" /tr "C:\ruta\al\proyecto\.venv\Scripts\python.exe C:\ruta\al\proyecto\src\etl.py" /sc hourly /mo 4
```

### Monitoreo de ejecuciones programadas

```bash
# Verificar ultima ejecución
python scripts/verify_etl.py

# Verificar que corrio en el horario esperado
tail -20 data/etl.log | grep "ETL COMPLETO"

# Verificar que no hay errores en el log de cron
tail -20 data/cron.log
```

## Comandos utiles para operacion diaria

### Verificacion rapida

```bash
python scripts/verify_etl.py
```

### Estadisticas de calidad

```bash
sqlite3 data/clinica_curated.db
SELECT
    COUNT(*) as total_citas,
    SUM(CASE WHEN is_no_show = 1 THEN 1 ELSE 0 END) as no_shows,
    ROUND(AVG(revenue_gap), 2) as avg_gap,
    ROUND(AVG(patient_age_at_visit), 0) as avg_age
FROM fact_appointments;
```

### Verificar rechazos por motivo

```bash
sqlite3 data/clinica_curated.db
SELECT
    reject_reason,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM quarantine), 2) as porcentaje
FROM quarantine
WHERE source = 'appointments'
GROUP BY reject_reason
ORDER BY cantidad DESC;
```

### Limpieza de datos de prueba

```bash
# Eliminar todo y empezar de nuevo
rm -rf data/volume_*
rm -f data/clinica_curated.db
rm -f data/watermark.json
rm -f data/etl.log
python scripts/seed_database.py
python src/etl.py
```

## Checklist de operacion diaria

- [ ] Verificar que el pipeline corrio en el horario programado
- [ ] Revisar `data/etl.log` en busca de errores o warnings
- [ ] Verificar que el quality gate paso (PASS en `etl_runs`)
- [ ] Confirmar que no hay registros en cuarentena con rechazos anormales
- [ ] Verificar que el watermark se actualizo correctamente
- [ ] Revisar metricas de calidad:
  - Tasa de rechazo < 30%
  - `unmatched_tarifa_rate` < 15%
  - `unmatched_patient_rate` < 15%
- [ ] Verificar que el numero de citas insertadas es razonable

</br>

# Referencia

**Se utilizó IA**

- **Herramienta:** Claude (Anthropic)
- **Uso realizado:** Apoyo en la definición del formato y estructura del runbook, asignación de responsables de escalamiento con base en información previamente proporcionada y generación/verificación de comandos para Windows.
- **Secciones donde se utilizó:** Formato del documento, sección de escalamiento y sección de comandos de Windows.
- **Validación realizada por el estudiante:** Se revisó la información generada por la IA y se validó que las asignaciones de escalamiento correspondieran con la información previamente proporcionada.
- **Otro (especifique):** La IA se utilizó como herramienta de apoyo; el contenido final fue revisado y ajustado por el estudiante.
