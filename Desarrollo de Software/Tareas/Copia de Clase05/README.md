# Clase 05 — Diseño y Construcción de Pipelines ETL

Esta carpeta contiene tres ejemplos de código que acompañan la presentación
de la Clase 5 (`Diseño y Construcción de Pipelines ETL para Sistemas de
Ciencia de Datos`), más un portal web (`portal_etl/`) para correrlos los
tres y ver en vivo qué etapa del pipeline se está ejecutando en cada uno.

```bash
cd portal_etl
./setup.sh && ./start.sh
# abrir http://127.0.0.1:5050
```

Para la práctica de laboratorio que se entrega a los alumnos (correr el
ejemplo 1 ya resuelto y construir los ejemplos 2 y 3 paso a paso), ver
[PRACTICA_GUIADA_ALUMNOS.md](PRACTICA_GUIADA_ALUMNOS.md).

Para la actividad evaluable donde los alumnos aplican el mismo proceso a
un escenario propio (no una copia de los ejemplos), ver
[ACTIVIDAD_EVALUABLE.md](ACTIVIDAD_EVALUABLE.md).

Los ejemplos 1 y 2 usan el mismo dominio (vehículos) que las clases
anteriores, con dos niveles de madurez de ingeniería distintos para que la
diferencia sea explícita en clase. El ejemplo 3 usa un dataset público real
para mostrar un caso de transformación de datos genuinamente sucio.

## `ejemplo_1_etl_basico/`

Un ETL mínimo: Extract → Transform → Load en un solo script, sin capa de
staging, sin contrato de datos formal, sin cuarentena, sin auditoría y sin
idempotencia. Corresponde a la Slide 1 de la presentación (¿qué es un ETL?)
y sirve como punto de partida "ingenuo" para contrastarlo después con el
ejemplo completo.

## `ejemplo_2_etl_completo/`

Un ETL que implementa el proceso completo usado durante la clase:

```text
DEFINE → EXTRACT → STAGE → VALIDATE → TRANSFORM → INTEGRATE → QUALITY GATE → LOAD → AUDIT
```

Incluye conceptos de las Slides 2 a 10: extracción incremental por
watermark, `batch_id`, contrato de datos con cuarentena de registros
inválidos, homologación e integración con reconciliación, quality gate con
umbrales, carga por `UPSERT` idempotente dentro de una transacción, y una
tabla de auditoría (`etl_runs`) que registra cada ejecución. Cierra con una
nota sobre cómo `vehicles_curated` alimentaría un Training Pipeline y un
Inference Pipeline, y el riesgo de Training-Serving Skew.

## `ejemplo_3_etl_duckdb/`

El mismo proceso, pero con motor **DuckDB** (patrón **ELT**: se carga
primero, se transforma después con SQL) y sobre el dataset público real
**Telco Customer Churn** (IBM). Expone dos problemas de calidad de datos
reales y no sintéticos: `TotalCharges` llega en blanco para clientes nuevos
(regla de negocio, no error) y varias columnas categóricas traen comillas
simples literales embebidas en el texto (dato sucio silencioso: un filtro
o `JOIN` "funciona" pero no compara lo que parece comparar).

Cada subcarpeta tiene su propio `README.md` con instrucciones de ejecución
(`./run_etl.sh` instala sus dependencias automáticamente). También se puede
correr cualquiera de los tres desde `portal_etl/`.
