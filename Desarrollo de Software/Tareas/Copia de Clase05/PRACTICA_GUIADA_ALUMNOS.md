# Práctica Guiada — Construye tus propios pipelines ETL

Esta práctica acompaña la Clase 5 (`Diseño y Construcción de Pipelines ETL
para Sistemas de Ciencia de Datos`). El objetivo no es copiar código: es
que construyas, con guía, tu propia versión de un ETL completo y de un
ETL con motor analítico (DuckDB) sobre un dataset real, aplicando el
proceso visto en clase:

```text
DEFINE -> EXTRACT -> STAGE -> VALIDATE -> TRANSFORM -> INTEGRATE
       -> QUALITY GATE -> LOAD -> AUDIT
```

## Qué se te entrega y qué debes construir

| | Se te entrega ya construido | Debes construirlo tú |
|---|---|---|
| Ejemplo 1 (ETL básico) | ✅ Código completo, para que lo corras y lo analices | — |
| Ejemplo 2 (ETL completo) | ❌ | ✅ Lo construyes siguiendo la Parte 2 de esta guía |
| Ejemplo 3 (ETL con DuckDB) | ❌ | ✅ Lo construyes siguiendo la Parte 3 de esta guía |

El ejemplo 1 se te da resuelto porque su propósito es que **veas primero
lo que le falta a un ETL mínimo**, antes de construir uno completo. Los
ejemplos 2 y 3 los construyes tú, en tu propia carpeta, siguiendo los
checkpoints de este documento. Cada checkpoint te dice qué debe pasar
cuando corres tu código en ese punto — si no coincide, no avances al
siguiente antes de corregirlo.

Al final de la práctica, tu profesor puede compartir la versión de
referencia para que compares decisiones de diseño, no para que la copies
antes de intentarlo.

---

## Parte 0 — Preparar el entorno

1. Crea tu propia carpeta de trabajo, por ejemplo:

   ```text
   mi_practica_etl/
     ejemplo_1_etl_basico/     <- aquí corres el ejemplo entregado
     ejemplo_2_etl_completo/   <- aquí construyes tu ETL completo
     ejemplo_3_etl_duckdb/     <- aquí construyes tu ETL con DuckDB
   ```

2. Crea un entorno virtual e instala las dependencias base:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pandas duckdb
   ```

3. Confirma que ambas librerías importan sin error:

   ```bash
   python -c "import pandas, duckdb; print('OK')"
   ```

---

## Parte 1 — Correr y analizar el Ejemplo 1 (ya resuelto)

No construyes nada en esta parte. El objetivo es que identifiques, **antes
de programar el ejemplo 2**, qué le falta a un ETL mínimo.

1. Corre `ejemplo_1_etl_basico/etl_basico.py` (o `./run_etl.sh` si tu
   profesor ya te lo compartió) y observa el log.
2. Abre el código y localiza las tres funciones: `extract()`,
   `transform()`, `load()`.
3. Responde por escrito, antes de seguir a la Parte 2:
   - ¿Dónde queda evidencia de los registros que `transform()` descarta?
   - ¿Cómo sabrías, sin volver a correr el script, cuántos registros tenía
     el archivo original en la última ejecución?
   - ¿Qué pasaría si este script corriera todos los días y el archivo de
     entrada creciera cada vez más?

Estas tres preguntas son exactamente lo que el Ejemplo 2 va a resolver.

---

## Parte 2 — Construye el Ejemplo 2: ETL completo (vehículos)

### Escenario

Vas a construir un pipeline con **tres fuentes** que conviven en la misma
carpeta de proyecto:

- **SQLite** — tabla `vehicles` (`vehicle_id`, `brand`, `model`, `year`,
  `mileage`, `mileage_unit`, `updated_at`).
- **CSV** — `market_prices.csv` (`vehicle_id`, `price`, `currency`,
  `source`, `observed_at`). Un vehículo puede tener varias filas de
  precio a través del tiempo.
- **JSON** — `manufacturers.json`, simulando una respuesta de API con
  `{brand: {country, segment}}`.

El destino final es una tabla `vehicles_curated` que un Training Pipeline
podría consumir después.

### Checkpoint A — DEFINE

Antes de escribir una sola línea de extracción, contesta por escrito
(esto va en un `config.json` que crearás):

1. **Grain**: ¿qué representa una fila en `vehicles_curated`? (Debe ser:
   un vehículo, con su información más reciente consolidada).
2. **Business key**: ¿qué campo identifica un vehículo de forma lógica?
   (`vehicle_id`).
3. **Refresh strategy**: ¿full o incremental? (Incremental, usando
   `updated_at` como watermark).
4. **Data contract** mínimo para `vehicles`:

   | Campo | Tipo | Regla |
   |---|---|---|
   | `vehicle_id` | Integer | Requerido, > 0 |
   | `year` | Integer | 1990 <= year <= año actual |
   | `mileage` | Float | >= 0 |

   Y para `market_prices`:

   | Campo | Tipo | Regla |
   |---|---|---|
   | `price` | Decimal | > 0 |
   | `currency` | Text | Debe estar en una lista de monedas permitidas |

5. **Failure strategy**: los registros inválidos van a cuarentena, no se
   descartan silenciosamente.

Crea `config.json` con, al menos, estas claves: rutas de las 3 fuentes,
nombre de la tabla de salida, nombre de la tabla de cuarentena, nombre de
la tabla de auditoría, año actual, monedas permitidas y umbrales de
calidad (ver Checkpoint F).

**No avances** hasta tener este archivo y poder cargarlo desde Python en
una estructura de configuración (por ejemplo, un `dataclass`).

### Checkpoint B — Datos semilla: de dónde salen y cómo generarlos

Los datos de este ejemplo son **sintéticos y tú los generas** con un
script `seed_database.py` (no se descargan de ningún lado). Para que tus
resultados de los checkpoints siguientes sean verificables, usa
exactamente esta tabla para poblar `vehicles`:

| `vehicle_id` | `brand` | `model` | `year` | `mileage` | `mileage_unit` | `updated_at` | Caso |
|---|---|---|---|---|---|---|---|
| 1 | Volkswagen | Golf | 2018 | 45000 | km | 2026-08-20T10:00:00 | válido |
| 2 | Nissan | Versa | 2020 | 28000 | km | 2026-08-20T10:05:00 | válido |
| 3 | Toyota | Corolla | 2019 | 32000 | km | 2026-08-20T10:10:00 | válido |
| 4 | Mazda | 3 | 2021 | 7500 | **mi** | 2026-08-20T10:15:00 | válido, prueba conversión de unidades |
| 5 | Honda | Civic | 2017 | 58000 | km | 2026-08-20T10:20:00 | válido, pero su precio será inválido |
| 6 | Volkswagen | Tiguan | 2016 | 62000 | km | 2026-08-20T10:25:00 | válido, pero su precio tendrá moneda no permitida |
| 7 | Nissan | Sentra | 2022 | 9000 | km | 2026-08-20T10:30:00 | válido |
| 8 | Kia | Rio | 2019 | 41000 | km | 2026-08-20T10:35:00 | válido, marca sin info de fabricante (unknown brand) |
| 9 | Toyota | Yaris | **2030** | 15000 | km | 2026-08-20T10:40:00 | inválido → `year_out_of_range` |
| 10 | Honda | CR-V | 2015 | **-500** | km | 2026-08-20T10:45:00 | inválido → `mileage_negative` |

Y esta tabla para `market_prices.csv` (columnas: `vehicle_id`, `price`,
`currency`, `source`, `observed_at`):

| `vehicle_id` | `price` | `currency` | `source` | `observed_at` | Caso |
|---|---|---|---|---|---|
| 1 | 185000 | MXN | market_a | 2026-08-18 | válido, no es la más reciente |
| 1 | 190000 | MXN | market_b | 2026-08-20 | válido, **es la más reciente** |
| 2 | 175000 | MXN | market_a | 2026-08-20 | válido |
| 3 | 200000 | MXN | market_a | 2026-08-19 | válido, no es la más reciente |
| 3 | 205000 | MXN | market_b | 2026-08-20 | válido, **es la más reciente** |
| 4 | 230000 | MXN | market_a | 2026-08-20 | válido |
| 5 | **-100** | MXN | market_a | 2026-08-20 | inválido → `price_invalid` |
| 6 | 210000 | **USD** | market_a | 2026-08-20 | inválido → `currency_not_allowed` (solo se permite `MXN`) |
| 7 | 165000 | MXN | market_a | 2026-08-20 | válido |
| 8 | 190000 | MXN | market_a | 2026-08-20 | válido |

Y este `manufacturers.json` (simulando la respuesta de una API), donde
`Kia` se deja **fuera a propósito** para forzar el caso de "marca sin
información de fabricante":

```json
{
  "Volkswagen": {"country": "Germany", "segment": "mainstream"},
  "Nissan": {"country": "Japan", "segment": "mainstream"},
  "Toyota": {"country": "Japan", "segment": "mainstream"},
  "Mazda": {"country": "Japan", "segment": "mainstream"},
  "Honda": {"country": "Japan", "segment": "mainstream"}
}
```

En tu `config.json`, define `current_year: 2026` y
`allowed_currencies: ["MXN"]` para que las reglas de arriba se cumplan
exactamente como están descritas.

Con estos datos, si tu código está correcto, en el Checkpoint D deberías
obtener **8 vehículos válidos y 2 en cuarentena**, y **8 filas de precio
válidas y 2 en cuarentena**. Si tus números no coinciden, no avances:
revisa primero si copiaste la tabla exactamente como está aquí.

### Checkpoint C — EXTRACT + STAGE

Escribe una función `extract()` que:

- Lea `vehicles` desde SQLite **filtrando por el watermark en la
  consulta SQL** (`WHERE updated_at > :watermark`), no en pandas después.
- Lea `market_prices.csv` completo.
- Lea `manufacturers.json` completo.

Escribe una función `stage()` que, **sin cambiar ningún valor de
negocio**, agregue a cada DataFrame de fuente:

- `source_system` (por ejemplo, `"sqlite:vehicles"`).
- `batch_id` (un identificador único de esta corrida, por ejemplo
  `ETL_20260824_020000`).
- `ingested_at` (timestamp de cuándo se extrajo).

✅ **Verificación de este checkpoint**: imprime el número de filas
extraídas y confirma que las tres columnas de metadatos existen en los
DataFrames staged, con el mismo `batch_id` en ambas fuentes.

### Checkpoint D — VALIDATE

Escribe una función `validate()` que, para cada fuente, calcule una razón
de rechazo (`rejection_reason`) por fila según el contrato del
Checkpoint A, y separe:

- Filas válidas → continúan.
- Filas inválidas → van a una tabla/DataFrame de **cuarentena**, con la
  fuente, el `batch_id`, el identificador del registro y el motivo.

✅ **Verificación**: con los datos sucios que sembraste en el Checkpoint
B, deberías ver en tu log algo como:

```text
VALIDATE: vehiculos validos=8 quarantine=2 | precios validos=8 quarantine=2
```

Si tu cuarentena queda vacía, revisa que tus datos semilla realmente
violen el contrato.

### Checkpoint E — TRANSFORM + INTEGRATE

En `transform()`, implementa al menos:

- Homologación de una columna categórica (por ejemplo, `brand`, usando un
  diccionario de alias). Con los datos del Checkpoint B las marcas ya
  vienen limpias, así que esto no cambiará nada visible por sí solo — si
  quieres comprobar que tu homologación realmente funciona, agrega
  temporalmente una fila con `brand = "VW"` y confirma que en
  `vehicles_curated` termina como `"Volkswagen"`.
- Conversión de unidades si `mileage_unit == "mi"` (millas a kilómetros).
  Esto lo vas a poder observar directamente con el vehículo 4 (Mazda 3),
  que sembraste con `mileage_unit = "mi"`.
- Una variable derivada: `vehicle_age = año_actual - year`.
- Selección de **la observación de precio más reciente por
  `vehicle_id`** (pista: `groupby("vehicle_id")["observed_at"].idxmax()`).
  Con los datos del Checkpoint B, los vehículos 1 y 3 tienen dos
  observaciones cada uno: debes quedarte con la de `2026-08-20`, no la de
  fecha anterior.

En `integrate()`:

- Combina vehículos con el precio más reciente (`merge(..., how="left")`).
- **Antes de continuar, verifica que el número de filas no haya
  cambiado respecto a los vehículos válidos.** Si cambió, algo está mal
  en la relación 1:N con precios y debes lanzar un error, no seguir
  adelante en silencio.
- Agrega país y segmento del fabricante desde `manufacturers.json`.
- Calcula un diccionario de **reconciliation**: `rows_before`,
  `rows_after`, `matched_with_price`, `unmatched_price`,
  `duplicated_vehicle_id`, `unknown_brand`.

✅ **Verificación**: con los datos del Checkpoint B, tu reconciliation
debe dar exactamente:

```text
rows_before=8, rows_after=8, matched_with_price=6, unmatched_price=2,
duplicated_vehicle_id=0, unknown_brand=1
```

`unmatched_price=2` corresponde a los vehículos 5 y 6 (su precio fue a
cuarentena). `unknown_brand=1` corresponde al vehículo 8 (Kia, que no
está en `manufacturers.json`). Si `rows_after != rows_before`, tu `merge`
está multiplicando filas — no continúes hasta entenderlo y corregirlo.

### Checkpoint F — QUALITY GATE

Define umbrales en `config.json` (por ejemplo:
`completeness_min: 0.90`, `duplicate_rate_max: 0.05`,
`unmatched_rate_max: 0.30`, `unknown_brand_rate_max: 0.20`) y escribe una
función `quality_gate()` que calcule esas cuatro métricas a partir del
resultado de `integrate()` y devuelva `PASS` o `FAIL`.

✅ **Verificación**: intenta bajar artificialmente un umbral (por ejemplo,
`unknown_brand_rate_max: 0.0`) y confirma que tu pipeline reporta `FAIL`
en vez de cargar los datos de todas formas.

### Checkpoint G — LOAD

Escribe una función `load()` que haga un **UPSERT** hacia
`vehicles_curated` (`INSERT ... ON CONFLICT(vehicle_id) DO UPDATE`),
dentro de una transacción (`with conn:` en `sqlite3`).

✅ **Verificación de idempotencia** (la prueba más importante de todo el
ejercicio):

1. Corre tu pipeline. Anota cuántas filas quedaron en `vehicles_curated`.
2. Sin cambiar los datos fuente, **resetea el watermark** a una fecha muy
   antigua y vuelve a correr el pipeline con el mismo batch de datos.
3. `vehicles_curated` debe tener **el mismo número de filas** que en el
   paso 1 (deben haberse actualizado, no duplicado).

Si el número de filas creció, tu `UPSERT` no está funcionando y estás
haciendo `INSERT` puro.

### Checkpoint H — AUDIT

Crea una tabla `etl_runs` (o `etl_audit`) con, al menos: `run_id`,
`started_at`, `finished_at`, cuántas filas se extrajeron, cuántas fueron
válidas, cuántas se pusieron en cuarentena, cuántas se insertaron/
actualizaron, y el `status` final (`SUCCESS` / `FAILED_QUALITY_GATE`).

✅ **Verificación final del Ejemplo 2**: corre tu pipeline 3 veces seguidas
(bootstrap, sin cambios, y reset de watermark) y confirma con una consulta
a `etl_runs` que quedaron 3 filas de auditoría distintas, con los conteos
esperados en cada una (la segunda corrida debe mostrar 0 filas
procesadas).

---

## Parte 3 — Construye el Ejemplo 3: ETL con DuckDB sobre un dataset real

### Por qué este ejemplo es distinto

En el Ejemplo 2 transformaste los datos **en pandas antes de guardarlos**
(patrón **ETL**). En este ejemplo vas a cargar el dato crudo primero y
transformarlo **con SQL dentro de DuckDB** (patrón **ELT**). Además, en
vez de datos sintéticos vas a trabajar con un dataset público real que
trae errores de datos genuinos.

Antes de seguir: si nunca has instalado `duckdb` en tu máquina, ve
primero a la sección **"Instalación paso a paso (y qué hacer si algo
falla)"** del [README del ejemplo 3](ejemplo_3_etl_duckdb/README.md).
Cubre entorno virtual, verificación de la instalación y los errores más
comunes (SSL/certificados, `ModuleNotFoundError`, permisos, versión de
Python incompatible). La mayoría de los problemas para "levantarlo" no
son de DuckDB, son de tener el Python equivocado activo en la terminal.

### Preparación: de dónde sale el dataset

A diferencia del Ejemplo 2, aquí **no generas los datos tú**: son un
dataset público real, "Telco Customer Churn" (IBM/Watson Analytics),
7,043 clientes de una compañía telefónica. Consíguelo con **una** de estas
dos opciones.

**Opción A — Descargarlo de Kaggle (recomendada si tienes cuenta):**

1. Entra a
   [kaggle.com/datasets/blastchar/telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
   (crea una cuenta gratuita si no tienes una).
2. Presiona **Download** y descomprime el archivo. El CSV se llama
   `WA_Fn-UseC_-Telco-Customer-Churn.csv`.
3. Cópialo a tu carpeta de práctica y renómbralo:

   ```bash
   mkdir -p ejemplo_3_etl_duckdb/data
   cp ~/Downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv \
      ejemplo_3_etl_duckdb/data/telco_churn.csv
   ```

   ⚠️ Esta versión de Kaggle **sí trae una columna `customerID`** como
   primera columna. Si descargas de aquí, usa `customerID` como
   *business key* directamente en el Checkpoint I, en vez de generar un
   `customer_id` sintético con `row_number()`.

**Opción B — Pedirlo a tu profesor (si no tienes acceso a Kaggle):**

El mismo archivo, ya sin la columna `customerID` (para forzar el
ejercicio de generar una business key sintética), es el que se usó en la
Clase 2 de este curso. Pide a tu profesor el archivo `telco_churn.csv` y
colócalo en `ejemplo_3_etl_duckdb/data/telco_churn.csv`. Con esta versión
sí sigues las instrucciones del Checkpoint I tal cual (generar
`customer_id` con `row_number()`), porque no hay `customerID` en el
archivo.

En cualquiera de las dos opciones, confirma que el archivo tiene 7,043
filas de datos (más el encabezado):

```bash
wc -l ejemplo_3_etl_duckdb/data/telco_churn.csv
```

### Inspección inicial (antes de escribir código)

Antes de programar nada, **inspecciona el archivo a mano**. Es la mejor
forma de descubrir el problema de datos que vas a resolver en el
Checkpoint J:

```bash
awk -F',' 'NR>1 && $5==0 {print $5, $18, $19}' ejemplo_3_etl_duckdb/data/telco_churn.csv | head
```

(Si tu archivo trae `customerID` como primera columna, ajusta los números
de columna del comando: todo se recorre una posición a la derecha).

Vas a encontrar filas donde `TotalCharges` es un espacio en blanco. Anota
en qué valor de `tenure` ocurre eso — lo vas a necesitar en el
Checkpoint J.

### Checkpoint I — DEFINE + EXTRACT/STAGE

1. **Grain**: una fila representa un cliente.
2. **Business key**: depende de qué versión del dataset conseguiste (ver
   "Preparación" arriba). Si tu archivo trae `customerID`, úsalo como
   business key. Si no trae ninguna columna identificadora (la versión
   sin `customerID`), vas a generar un `customer_id` sintético.
3. **Refresh strategy**: full load (es un snapshot, no hay columna de
   fecha de actualización).
4. Conecta a un archivo DuckDB (`duckdb.connect("data/telco.duckdb")`) y,
   en **una sola sentencia SQL**, crea una tabla de staging que:

   - Lea el CSV con `read_csv_auto`.
   - Si no tienes `customerID`, genera un `customer_id` sintético con
     `row_number() OVER ()`. Si sí tienes `customerID`, úsalo tal cual.
   - Fuerce `TotalCharges` a tipo `VARCHAR` explícitamente (no dejes que
     DuckDB adivine el tipo — hazlo explícito en el `read_csv_auto`).
   - Agregue `source_system`, `batch_id`, `ingested_at`.

✅ **Verificación**: `SELECT count(*) FROM stg_customers` debe dar 7,043.
Ejecuta también `DESCRIBE stg_customers` y observa qué tipo le asignó
DuckDB a columnas como `Partner`, `Dependents` o `Churn` — vas a necesitar
saberlo para el Checkpoint K.

### Checkpoint J — VALIDATE (el caso interesante #1)

Antes de "arreglar" el problema de `TotalCharges`, investígalo con SQL:

```sql
SELECT tenure, count(*) FROM stg_customers
WHERE trim(TotalCharges) = ''
GROUP BY tenure;
```

Vas a confirmar que **todas** las filas con `TotalCharges` en blanco
tienen `tenure = 0`. Esto es una pista de negocio, no un error aleatorio:
son clientes recién dados de alta que todavía no han sido facturados.

Con esa evidencia, escribe tu `VALIDATE` para que:

- Mande a **cuarentena** cualquier fila con `TotalCharges` en blanco
  **y** `tenure != 0` (en este dataset no debería haber ninguna, pero tu
  validación debe cubrir el caso).
- **No** mande a cuarentena las filas con `TotalCharges` en blanco y
  `tenure = 0` — esas se corrigen en `TRANSFORM`, no se descartan.
- También valide `MonthlyCharges > 0`.

### Checkpoint K — TRANSFORM (el caso interesante #2)

Antes de escribir la limpieza, comprueba con una consulta si esto pasa en
tu copia del dataset:

```sql
SELECT * FROM stg_customers WHERE PaymentMethod = 'Electronic check';
```

Si el resultado da **0 filas** aunque el preview de la tabla "se vea"
igual, tienes comillas simples literales embebidas en el texto (por
ejemplo, el valor real es `'Electronic check'`, con comillas incluidas).
Confírmalo con:

```sql
SELECT DISTINCT PaymentMethod FROM stg_customers LIMIT 5;
```

En tu `TRANSFORM`, limpia esas columnas con `trim(x, '''')` (quita
comillas simples de los extremos) seguido de un `trim` normal (quita
espacios). Aplica esto a **todas** las columnas categóricas que lo
necesiten (revisa `MultipleLines`, `PaymentMethod` y `Contract`).

Además, en la misma etapa:

- Convierte `TotalCharges` a `DOUBLE`, con la regla de negocio del
  Checkpoint J (`tenure = 0` → `0.0`).
- Crea `tenure_bucket` con un `CASE` (por ejemplo: `0-12`, `13-24`,
  `25-48`, `49+`).
- Calcula `avg_monthly_spend` (cuidado con dividir entre `tenure = 0`).

✅ **Verificación**: consulta un par de filas de tu tabla transformada y
confirma que ningún valor de `payment_method` o `contract` empieza o
termina con una comilla simple.

### Checkpoint L — INTEGRATE con dos grains

A diferencia del Ejemplo 2, aquí **no integras varias fuentes**: integras
el mismo dato en **dos niveles de agregación** para dos consumidores
distintos:

1. `customers_curated` — grain = cliente. Pensado para un Training
   Pipeline.
2. `churn_by_segment_curated` — grain = segmento (`contract` x
   `tenure_bucket`), con `customers`, `churned`, `churn_rate` y
   `avg_monthly_spend` agregados por segmento. Pensado para un dashboard
   de Analytics.

✅ **Verificación**: la suma de `customers` en `churn_by_segment_curated`
debe ser igual al total de filas en `customers_curated`.

### Checkpoint M — QUALITY GATE, LOAD y AUDIT

Igual que en el Ejemplo 2, pero con una diferencia importante: como este
es un **full load**, la idempotencia se logra reemplazando la tabla
completa (`CREATE OR REPLACE TABLE`), no con `UPSERT`.

- Define umbrales de `completeness`, `quarantine_rate`, y agrega un
  **rango de sanity check** para `churn_rate` (por ejemplo, entre 0.05 y
  0.60) — si el churn rate calculado estuviera fuera de ese rango, algo
  está mal en tu pipeline, aunque técnicamente no haya lanzado ninguna
  excepción.
- Además de guardar en DuckDB, exporta ambas tablas curated a **Parquet**
  con `COPY ... TO '...' (FORMAT PARQUET)`.
- Registra cada corrida en una tabla `etl_runs`.

✅ **Verificación final del Ejemplo 3**: corre tu pipeline dos veces
seguidas. `customers_curated` debe tener el mismo número de filas en
ambas corridas (7,043), y `etl_runs` debe tener 2 registros.

---

## Entregable

Al terminar, tu carpeta de práctica debe contener, como mínimo:

```text
ejemplo_2_etl_completo/
  config.json
  seed_database.py
  etl_completo.py
  data/  (generado al correr seed_database.py)

ejemplo_3_etl_duckdb/
  etl_duckdb.py
  data/telco_churn.csv
  data/telco.duckdb          (generado al correr tu pipeline)
  data/customers_curated.parquet
  data/churn_by_segment_curated.parquet
```

Junto con tu código, entrega un archivo corto (`NOTAS.md`) respondiendo:

1. ¿Qué decidiste como `grain` y `business key` en cada ejemplo, y por
   qué?
2. En el Ejemplo 3, explica con tus palabras por qué el blanco en
   `TotalCharges` no se trató como un error.
3. ¿Qué pasaría si, en el Ejemplo 2, quitaras la validación de
   cardinalidad en `integrate()`? Descríbelo con un ejemplo numérico.
4. ¿En qué se diferencia, en tu código, la idempotencia del Ejemplo 2
   (incremental + UPSERT) de la del Ejemplo 3 (full load + reemplazo)?
