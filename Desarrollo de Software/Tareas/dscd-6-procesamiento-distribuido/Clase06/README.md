# Módulo 02 — Apache Spark: Procesamiento Distribuido para Pipelines de Datos

**Prof: Alder López Cerda, PhD**

 módulo de la línea [`AI-Pipeline`](../README.md). Cubre el motor de procesamiento distribuido (Spark) que se usa para escalar la etapa de ETL cuando el volumen de datos deja de caber cómodamente en una sola máquina.

## Objetivo del módulo

Que el alumno entienda:
1. **Cuándo** conviene usar Spark (y cuándo NO — no es la respuesta por defecto a "datos grandes").
2. **Cómo** Spark distribuye el trabajo (Partition, Job, Stage, Task, Driver/Executor/Cluster Manager).
3. **Por qué** algunas operaciones son mucho más costosas que otras (Shuffle, Data Skew, Wide vs. Narrow transformations).
4. **Cómo llevarlo a producción** con buenas prácticas: testing, configuración de recursos, resiliencia y observabilidad de costos.

Todo sobre un único caso conductor: una empresa que procesa información de vehículos, escalando de 2 GB/día a 500 GB/día + 3 TB históricos.


### Actividad Práctica Evaluada — [ACTIVIDAD_PRACTICA_SPARK.md](ACTIVIDAD_PRACTICA_SPARK.md)

Guía detallada paso a paso para ejecutar la actividad evaluada de Spark. Incluye el **Benchmark de Escalabilidad (Pandas vs PySpark)** en 5 volúmenes de datos, el análisis del **Punto de Inflexión (*Crossover Point*)**, la ejecución de los ejemplos productivos completos y la lista de evidencias requeridas.

### Práctica guiada — [spark-clase/](spark-clase/)

Carpeta con 8 scripts progresivos de PySpark ejecutables en `local[*]` (sin necesitar clúster real), más datos de ejemplo y su propio [`README.md`](spark-clase/README.md) con guía paso a paso, preguntas de observación por script y troubleshooting.

| Script | Cubre |
|--------|-------|
| `01_hello_spark.py` | Primera SparkSession |
| `02_dataframe.py` | Lectura y exploración de un DataFrame |
| `03_transformations.py` | Transformation vs. Action, Execution Plan |
| `04_aggregations.py` | Agregaciones y aparición del Shuffle (`Exchange`) |
| `05_join.py` | JOIN normal vs. Broadcast Join |
| `06_spark_sql.py` | La misma lógica en Spark SQL |
| `07_etl_pipeline.py` | Pipeline ETL completo con Quality Gates |
| `08_produccion.py` | **Buenas prácticas**: AQE, lectura tolerante a corruptos, escritura idempotente, patrón de testing sin pytest |

### Automatización de entorno — [`setup_spark.sh`](setup_spark.sh)

Script idempotente que deja lista toda la práctica de un solo comando: verifica/instala Python y Java, crea el venv, instala PySpark, genera los datos de ejemplo (con skew intencional para poder observarlo), genera los 7 scripts base + un script adicional de monitoreo (`08_hold_spark_ui.py`, que detiene la ejecución para inspeccionar Spark UI con calma), corre un smoke test, y deja un `run_all.sh` que ejecuta y valida toda la práctica de punta a punta.

```bash
chmod +x setup_spark.sh
./setup_spark.sh            # crea ./spark-clase desde cero
./setup_spark.sh --force    # regenera todo (venv, datos, scripts)
```

> Nota: `setup_spark.sh` genera su propia copia de los scripts 01–07 y agrega `08_hold_spark_ui.py` (enfocado en monitoreo interactivo vía Spark UI). Esto es complementario al `08_produccion.py` ya incluido en `spark-clase/` (enfocado en configuración/testing/resiliencia) — **no se sobrescriben entre sí** porque tienen nombres distintos, pero si corres `setup_spark.sh` sobre la carpeta `spark-clase/` ya existente, revisa que no dupliques intención entre ambos "08".

## Requisitos

- Python 3.9–3.12
- Java 8, 11 o 17 (⚠️ ver nota de compatibilidad abajo)
- PySpark 3.5.1 (se instala automáticamente vía `setup_spark.sh` o `pip install -r spark-clase/requirements.txt`)

### ⚠️ Compatibilidad de Java

PySpark 3.5.x **no es compatible con Java 21+** (incluyendo Java 25, el default en macOS recientes). Si `pyspark` falla con `UnsupportedOperationException: getSubject is not supported`, apunta `JAVA_HOME` a una versión soportada antes de correr cualquier script:

```bash
/usr/libexec/java_home -V                        # lista versiones instaladas
export JAVA_HOME=$(/usr/libexec/java_home -v 17)  # o -v 11, -v 1.8
```

Vale la pena advertir esto a los alumnos **antes** de la práctica en vivo — es el error más probable en máquinas con Java recién instalado.



## Conexión con el resto del pipeline

El resultado curado de este módulo (`output/vehicles_curated/`, Parquet particionado por año) es, conceptualmente, el insumo que alimentaría el módulo **03-Entrenamiento** de la línea `AI-Pipeline` — mismo caso conductor, siguiente etapa del pipeline.
