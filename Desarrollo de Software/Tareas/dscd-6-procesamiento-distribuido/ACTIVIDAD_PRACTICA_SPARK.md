# Actividad Práctica Evaluada: Benchmark de Escalabilidad y Pipeline ETL con Apache Spark

**Módulo**: Apache Spark - Procesamiento Distribuido para Pipelines de Datos  
**Asignatura**: TC3009C - AI-Pipeline  

---

## 1. Objetivo de la Actividad

1. **Evaluar el umbral de escala entre Pandas y Apache Spark**: Identificar experimentalmente en qué volumen de datos PySpark supera a Pandas en tiempo de ejecución y eficiencia de memoria.
2. **Medir el Punto de Inflexión (*Crossover Point*)**: Cuantificar el costo fijo de inicialización (*overhead*) de Apache Spark en comparación con el procesamiento monohilo en memoria de Pandas.
3. **Ejecutar e inspeccionar pipelines ETL productivos**: Correr pipelines distribuidos completos con Quality Gates, manejo de registros corruptos, escrituras idempotentes y monitoreo en Spark UI.

---

## 2. Requisitos Previos

Ejecutar el script de automatización desde la raíz de `Clase06` para preparar el entorno:

```bash
cd Clase06
chmod +x setup_spark.sh
./setup_spark.sh
```

> **Nota sobre Java en macOS**: PySpark 3.5.x requiere Java 8, 11 o 17 (no soporta Java 21+). En caso de error de JVM, definir la variable de entorno:
> ```bash
> export JAVA_HOME=$(/usr/libexec/java_home -v 17)
> ```

---

## 3. Parte 1: Benchmark Comparativo de Escalabilidad (Pandas vs. PySpark)

Se ejecutará un barrido experimental comparando el pipeline en Pandas ([pandas_etl.py](benchmark-pandas-vs-spark/pandas_etl.py)) contra PySpark ([spark_etl.py](benchmark-pandas-vs-spark/spark_etl.py)).

### 3.1 Matriz de Experimentos

Se realizará un barrido de **7 experimentos** estructurados para localizar con precisión el punto de convergencia y documentar **3 victorias técnicas consecutivas donde Spark es superior a Pandas**:

| Experimento | Filas (`--rows`) | Tamaño aprox. CSV | Comportamiento Esperado | Resultado / Ganador |
| :--- | :--- | :--- | :--- | :--- |
| **Exp 1** | `50,000` (50K) | ~1.5 MB | Overhead dominante de inicialización JVM/Spark (~50s). | **Pandas gana** (< 2s vs ~53s) |
| **Exp 2** | `2,000,000` (2M) | ~63 MB | Pandas procesa rápido en RAM en un solo hilo. | **Pandas gana** (~13s vs ~56s) |
| **Exp 3** | `5,000,000` (5M) | ~160 MB | Reducción acelerada de la brecha de tiempo. | **Aproximación** (~30s vs ~58s) |
| **Exp 4** | `10,000,000` (10M) | ~320 MB | **Punto de Convergencia / Inflexión (Crossover Point)**. Tiempos de ejecución se igualan. | **Empate / Punto Inflexión** (~60s vs ~60s) |
| **Exp 5** | `20,000,000` (20M) | ~650 MB | **Victoria Spark 1 (Cómputo multihilo)**: Paralelización en cores superando overhead de inicio. | **Spark gana** (~68s vs ~130s) |
| **Exp 6** | `35,000,000` (35M) | ~1.1 GB | **Victoria Spark 2 (Escalabilidad lineal)**: Rendimiento constante vs degradación por Garbage Collector de Pandas. | **Spark gana** (~78s vs ~230s) |
| **Exp 7** | `50,000,000` (50M) | ~1.6 GB | **Victoria Spark 3 (Resiliencia RAM)**: Manejo de Spill to Disk evitando crash por Out Of Memory (OOM). | **Spark gana** (~85s vs OOM / >350s) |

> **Nota metodológica sobre hardware**: El punto de convergencia exacto se ubica típicamente entre **5M y 15M de filas** dependiendo de la cantidad de núcleos CPU de la máquina. Si en tu equipo con 10M filas aún no se cruzan los tiempos, ajusta el experimento intermedio a 12M o 15M hasta visualizar el punto de intersección gráfica.

### 3.2 Análisis de los 3 Escenarios de Superioridad Técnica de Spark

El benchmark demuestra 3 ventajas arquitectónicas de Apache Spark frente a Pandas al escalar datos:

1. **Escenario 1 — Ganancia por Paralelismo Multihilo (20M filas / ~650 MB)**  
   Pandas está limitado a la ejecución monohilo de C/Python. Al sobrepasar los 20M de filas, PySpark distribuye las particiones sobre todos los núcleos lógicos del procesador (`local[*]`), reduciendo el tiempo de procesamiento a la mitad en comparación con Pandas.

2. **Escenario 2 — Escalamiento Lineal vs. Degradación de Recolección de Basura (35M filas / ~1.1 GB)**  
   Al superar 1 GB de datos plano, Pandas sufre ralentización por la gestión de memoria interna de Python y la fragmentación de tipos en NumPy. PySpark utiliza ejecución estructurada mediante el motor **Catalyst / Tungsten**, manteniendo un tiempo de procesamiento lineal sin sobrecalentamiento de RAM.

3. **Escenario 3 — Resiliencia a Limite de RAM vía *Spill-to-Disk* (50M filas / ~1.6 GB)**  
   Pandas requiere entre 3x y 5x el tamaño del archivo en memoria para realizar operaciones como JOIN y Agregación, provocando un error de Kernel por falta de memoria (Out of Memory - OOM). PySpark gestiona los bloques de memoria volcando excesos al disco (*spill to disk*) mediante evaluacion perezosa (*lazy evaluation*), garantizando la finalización exitosa del trabajo.

### 3.3 Comandos de Ejecución

Navegar al directorio del benchmark:
```bash
cd Clase06/benchmark-pandas-vs-spark
```

Ejecutar la secuencia para cada uno de los 7 experimentos:

#### Experimento 1 (50K filas):
```bash
python generate_data.py --rows 50000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_50k.json
```

#### Experimento 2 (2M filas):
```bash
python generate_data.py --rows 2000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_2m.json
```

#### Experimento 3 (5M filas - Aproximación):
```bash
python generate_data.py --rows 5000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_5m.json
```

#### Experimento 4 (10M filas - Punto de Convergencia):
```bash
python generate_data.py --rows 10000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_10m.json
```

#### Experimento 5 (20M filas - Victoria Spark 1: Multihilo):
```bash
python generate_data.py --rows 20000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_20m.json
```

#### Experimento 6 (35M filas - Victoria Spark 2: Escalamiento):
```bash
python generate_data.py --rows 35000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_35m.json
```

#### Experimento 7 (50M filas - Victoria Spark 3: Resiliencia OOM):
```bash
python generate_data.py --rows 50000000 --out-dir data
python run_benchmark.py --data-dir data --out-json benchmark_result_50m.json
```

---

## 4. Parte 2: Pipeline Completo y Prácticas de Producción en PySpark

Navegar al directorio de scripts de clase:
```bash
cd ../spark-clase
```

### 4.1 Secuencia de Ejecución

1. **Ejecución de scripts base (01 a 06)**:
   Analizar transformaciones, agregaciones, tipos de JOIN y planes de ejecución (Physical Plan / Catalyst):
   ```bash
   python 01_hello_spark.py
   python 03_transformations.py
   python 04_aggregations.py
   python 05_join.py
   ```

2. **Pipeline ETL con Quality Gates ([07_etl_pipeline.py](spark-clase/07_etl_pipeline.py))**:
   Ejecutar el pipeline con validación de esquema, nulos y rangos:
   ```bash
   python 07_etl_pipeline.py
   ```

3. **Script de Producción ([08_produccion.py](spark-clase/08_produccion.py))**:
   Ejecutar el pipeline con patrones avanzados:
   ```bash
   python 08_produccion.py
   ```
   Componentes evaluados en este script:
   - Adaptive Query Execution (AQE).
   - Manejo de registros corruptos con modalidad `PERMISSIVE` y `badRecordsPath`.
   - Escritura idempotente particionada.
   - Pruebas unitarias de transformaciones sobre DataFrames de Spark.

4. **Inspección en Spark UI**:
   Iniciar el script de retención del proceso:
   ```bash
   python 08_hold_spark_ui.py
   ```
   Abrir `http://localhost:4040` en el navegador e inspeccionar *Jobs*, *Stages*, *DAG Visualization* y métricas de *Shuffle*.

---

## 5. Monitoreo de Recursos y Tabla Consolidada de Reporte

### 5.1 Métricas de Monitoreo Obligatorias

Para cada experimento ejecutado en el benchmark, se deben registrar las siguientes métricas de monitoreo de sistema por cada modo de ejecución (**Modo Tradicional - Pandas** vs. **Modo Distribuido - PySpark**):

1. **Hora de Inicio (`start_time`)**: Estampa de tiempo exacta (YYYY-MM-DD HH:MM:SS) al comenzar la ejecución del script.
2. **Hora de Fin (`end_time`)**: Estampa de tiempo exacta (YYYY-MM-DD HH:MM:SS) al finalizar el proceso.
3. **Duración Total (`wall_time_s`)**: Tiempo total transcurrido (*wall clock time*) expresado en segundos.
4. **Uso de Memoria Pico (`peak_memory_mb`)**: Máximo consumo de memoria RAM registrado por el proceso en MB / GB.
5. **Uso Promedio de CPU (%)**: Porcentaje promedio de uso de núcleos procesadores durante la ejecución (100% representa 1 núcleo saturado; multihilo puede superar el 100%).

### 5.2 Tabla Consolidada de Resultados de Benchmark

Como elemento central del reporte entregable, se debe completar la siguiente tabla comparativa incorporando las métricas de monitoreo extraídas de los archivos `.json` generados por `run_benchmark.py`:

| Exp | Modo / Motor | Filas (`rows`) | Tamaño CSV | Hora Inicio | Hora Fin | Duración Total (s) | Memoria Pico (MB) | Uso CPU Est. (%) | Ganador / Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Exp 1** | Pandas (Tradicional)<br>PySpark (Distribuido) | 50,000 | ~1.5 MB | | | | | Monohilo (~100%)<br>Multihilo (Overhead) | **Pandas gana** |
| **Exp 2** | Pandas (Tradicional)<br>PySpark (Distribuido) | 2,000,000 | ~63.3 MB | | | | | Monohilo (~100%)<br>Multihilo (Parcial) | **Pandas gana** |
| **Exp 3** | Pandas (Tradicional)<br>PySpark (Distribuido) | 5,000,000 | ~160 MB | | | | | Monohilo (~100%)<br>Multihilo (Parcial) | **Aproximación** |
| **Exp 4** | Pandas (Tradicional)<br>PySpark (Distribuido) | 10,000,000 | ~320 MB | | | | | Monohilo (~100%)<br>Multihilo (Cálculo) | **Punto de Inflexión** |
| **Exp 5** | Pandas (Tradicional)<br>PySpark (Distribuido) | 20,000,000 | ~650 MB | | | | | Monohilo (~100%)<br>Multihilo (>300%) | **Spark (Victoria 1 - Multihilo)** |
| **Exp 6** | Pandas (Tradicional)<br>PySpark (Distribuido) | 35,000,000 | ~1.1 GB | | | | | Monohilo (~100%)<br>Multihilo (>400%) | **Spark (Victoria 2 - Escalamiento)** |
| **Exp 7** | Pandas (Tradicional)<br>PySpark (Distribuido) | 50,000,000 | ~1.6 GB | | | | | OOM / Saturación<br>Spill to Disk | **Spark (Victoria 3 - Resiliencia RAM)** |

### 5.3 Especificación Detallada de Archivos de Salida y Resultados Esperados

A continuación se detallan los archivos específicos que se deben generar, mostrar y entregar, indicando el contenido exacto que se espera de cada uno:

#### 1. Archivos JSON de Benchmark (`benchmark_result_*.json`)
* **Ubicación**: `Clase06/benchmark-pandas-vs-spark/`
* **Archivos requeridos**: `benchmark_result_50k.json`, `benchmark_result_2m.json`, `benchmark_result_5m.json`, `benchmark_result_10m.json`, `benchmark_result_20m.json`, `benchmark_result_35m.json`, `benchmark_result_50m.json`.
* **Contenido esperado a verificar**:
  * `rows`: Conteo total de filas procesadas.
  * `csv_size_mb`: Tamaño del archivo CSV de entrada en MB.
  * `pandas`: Bloque con `start_time`, `end_time`, `wall_time_s`, `peak_memory_mb` y `returncode` (0 indica éxito).
  * `spark`: Bloque con `start_time`, `end_time`, `wall_time_s`, `reported_total_s` y `returncode`.

#### 2. Estructura de Salida Parquet Particionado (`output_spark/vehicles_curated/`)
* **Ubicación**: `Clase06/spark-clase/output/vehicles_curated/` y `Clase06/benchmark-pandas-vs-spark/output_spark/vehicles_curated/`
* **Estructura esperada a mostrar**:
  * Archivo de control `_SUCCESS` (confirma la finalización exitosa del Job de Spark).
  * Directorios de partición física nombrados por columna de partición: `year=2015/`, `year=2016/`, ..., `year=2024/`.
  * Dentro de cada carpeta de año: Archivos binarios comprimidos en formato Parquet (ejemplo: `part-00000-...snappy.parquet`).

#### 3. Salida de Consola del Pipeline ETL (`07_etl_pipeline.py`)
* **Ubicación / Medio**: Captura de terminal o log de ejecución.
* **Contenido esperado a verificar**:
  * Resumen tabular agrupado por marca (`summary.show(20)`).
  * Conteo exacto de registros en el reporte de auditoría:
    * Registros originales (ej. 1,005).
    * Registros válidos (ej. 1,000).
    * Registros rechazados por Quality Gates (ej. 5 registros corruptos/inválidos).
    * Registros escritos en el almacenamiento curado.

#### 4. Interfaz Gráfica de Spark UI (`http://localhost:4040`)
* **Ubicación / Medio**: Capturas de pantalla durante la ejecución de `08_hold_spark_ui.py`.
* **Detalles esperados a mostrar**:
  * **Pestaña Jobs / Stages**: Visualización del estado Completed de los Stages, mostrando la distribución de Tasks entre núcleos procesadores.
  * **DAG Visualization**: Grafo Acíclico Dirigido evidenciando la separación entre transformaciones estrechas (*Narrow*) y operaciones con *Shuffle/Exchange* (*Wide*).
  * **Pestaña SQL/DataFrame**: Plan físico desplegado con Catalyst indicando el uso de `BroadcastHashJoin` o `SortMergeJoin`.

---

## 6. Preguntas de Análisis

1. Explique las razones técnicas por las cuales Pandas es más rápido que PySpark en volúmenes pequeños (50K - 500K filas), considerando el overhead de inicialización de la JVM, SparkContext y Catalyst Optimizer.
2. Identifique el rango de filas y tamaño en MB donde se presentó el Punto de Inflexión (*Crossover Point*) en su entorno de ejecución.
3. Compare el comportamiento del consumo pico de memoria RAM de Pandas contra el de PySpark a medida que incrementó el volumen de datos.
4. Describa las ventajas de almacenar el resultado final en formato Parquet particionado en comparación con un archivo CSV único.

---

## 7. Criterios de Evaluación

| Criterio | Ponderación |
| :--- | :---: |
| Ejecución de los 7 experimentos del benchmark y entrega de los 7 archivos JSON | 25% |
| Elaboración de la gráfica comparativa con identificación del *Crossover Point* | 20% |
| Capturas de evidencia (Consola, Spark UI y directorio Parquet) | 20% |
| Ejecución y análisis de los scripts de producción (`07_etl_pipeline.py` y `08_produccion.py`) | 20% |
| Respuestas a las preguntas de análisis | 15% |

