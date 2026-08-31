# Práctica guiada — Spark local paso a paso

Material de apoyo para las slides 7 a 15 de la clase
**"Apache Spark: Procesamiento Distribuido para Pipelines de Datos"**.

Caso conductor: procesamiento de información de vehículos (`vehicles.csv`)
relacionada con su fabricante (`manufacturers.csv`).

## Estructura del proyecto

```
spark-clase/
│
├── README.md
├── requirements.txt
├── data/
│   ├── vehicles.csv         (2,000 registros, distribución desigual por marca)
│   └── manufacturers.csv    (10 registros)
├── 01_hello_spark.py
├── 02_dataframe.py
├── 03_transformations.py
├── 04_aggregations.py
├── 05_join.py
├── 06_spark_sql.py
├── 07_etl_pipeline.py
├── 08_produccion.py
├── requirements-dev.txt      (opcional, solo referencia para testing con pytest)
└── output/                  (se genera al ejecutar 07_etl_pipeline.py y 08_produccion.py)
```

`vehicles.csv` se generó con una distribución intencionalmente desigual
entre marcas (Toyota y Nissan concentran la mayoría de los registros,
Ferrari muy pocos) para poder observar Data Skew en la slide 12 sin
depender de datos externos.

## Preparación del ambiente

Ver también la slide 7 ("Preparar Spark localmente").

```bash
python3 --version
java -version

mkdir spark-clase
cd spark-clase

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

No es necesario instalar Hadoop ni construir un clúster para esta
práctica: todo se ejecuta en `local[*]`, es decir, en la misma
computadora.

## Ejecución de los scripts

Ejecutar en orden, con el ambiente virtual activo:

```bash
source .venv/bin/activate

python 01_hello_spark.py
python 02_dataframe.py
python 03_transformations.py
python 04_aggregations.py
python 05_join.py
python 06_spark_sql.py
python 07_etl_pipeline.py
python 08_produccion.py
```

Mientras cualquiera de estos scripts está en ejecución (antes de que
llegue a `spark.stop()`), la aplicación expone Spark UI, normalmente
en:

```
http://localhost:4040
```

Si el puerto está ocupado, Spark UI puede abrirse en 4041, 4042, etc.
La consola imprime la URL exacta al iniciar la SparkSession.

## Qué debe observar el estudiante

- **Transformation vs. Action**: en `03_transformations.py`, notar que
  construir `recent` no imprime nada; solo `show()` y `count()`
  provocan ejecución (Lazy Evaluation).
- **Número de Partitions**: en `02_dataframe.py`, comparar
  `df.rdd.getNumPartitions()` con el número de cores locales
  disponibles.
- **Execution Plan**: en `03_transformations.py` y `06_spark_sql.py`,
  leer el Physical Plan y ubicar el scan, los filters y la
  agregación.
- **Aparición de Exchange/Shuffle**: en `04_aggregations.py`, buscar
  el operador `Exchange` en el plan — es la marca de un Shuffle
  producido por `groupBy`.
- **Estrategia del JOIN**: en `05_join.py`, comparar el plan del JOIN
  normal contra el plan con `broadcast()` y ubicar
  `BroadcastExchange`.
- **Jobs y Stages en Spark UI**: ejecutar `result.count()` (o
  cualquier Action) con Spark UI abierta, e identificar cuántos Jobs
  y Stages se generaron, cuántas Tasks tiene cada Stage y si aparece
  Shuffle Read/Write.
- **Reporte de calidad**: en `07_etl_pipeline.py`, comparar registros
  originales, válidos, rechazados y escritos.
- **Buenas prácticas de producción**: en `08_produccion.py`, revisar
  `spark.sql.adaptive.enabled` y `spark.sql.shuffle.partitions` en el
  builder, el manejo de registros corruptos con `mode="PERMISSIVE"` y
  `columnNameOfCorruptRecord`, la escritura idempotente con
  `partitionOverwriteMode="dynamic"`, y el bloque `if __name__ ==
  "__main__":` que prueba `validar_reglas()` de forma aislada, sin
  pytest, como ejemplo del patrón de testing descrito en la clase.

## Errores comunes durante la práctica

- **Java no encontrado**: revisar que Java esté instalado y que la
  versión sea compatible con la versión de PySpark de
  `requirements.txt`.
- **Java demasiado nuevo (ej. Java 21+/25) rompe PySpark 3.5.x**:
  en macOS con varias versiones de Java instaladas, error típico
  `UnsupportedOperationException: getSubject is not supported`.
  Apuntar `JAVA_HOME` a una versión 8, 11 o 17 antes de ejecutar:
  `export JAVA_HOME=$(/usr/libexec/java_home -v 17)` (o `-v 1.8`,
  `-v 11`, según lo que tengas instalado con
  `/usr/libexec/java_home -V`).
- **Ambiente virtual no activado**: si `pyspark` no se encuentra al
  ejecutar un script, confirmar que `.venv` esté activo
  (`source .venv/bin/activate`).
- **Archivo no encontrado**: los scripts asumen que se ejecutan desde
  la raíz de `spark-clase/`, donde vive la carpeta `data/`.
- **Schema inferido incorrectamente**: si una columna numérica se lee
  como string, revisar que `inferSchema` esté en `True` y que el CSV
  no tenga valores inconsistentes en esa columna.
- **Puerto de Spark UI ocupado**: si 4040 está en uso, Spark asigna
  automáticamente el siguiente puerto disponible; revisar la consola
  para confirmar cuál se usó.
- **Uso accidental de `collect()` sobre datasets grandes**:
  `collect()` mueve todos los resultados al Driver. Sobre un dataset
  grande, esto puede agotar la memoria del Driver. En esta práctica
  no es necesario usar `collect()`; `show()`, `count()` y `write`
  son suficientes.
