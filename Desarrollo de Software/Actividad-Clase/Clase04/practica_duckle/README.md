# Practica minima de Duckle: integrar precios de vehiculos

## Antes de integrar: primera ejecucion

Empieza por [README_INICIAL.md](README_INICIAL.md). Es una demostracion corta
de:

```text
CSV → Filter → CSV
```

Su objetivo es explicar que hace Duckle, para que sirve una fuente, que es una
transformacion, que es un sink y como observar una corrida. No avances al join
SQLite + CSV hasta que esta primera salida tenga 4 filas.

La salida esperada se puede verificar con:

```bash
python verify_initial_demo.py
```

Ese comando solo funcionara despues de ejecutar el pipeline inicial en Duckle.

## Objetivo

Construir visualmente un pipeline que tome informacion de una base SQLite y un
CSV de precios de mercado, integre ambas fuentes, descarte registros invalidos
y escriba un resultado en SQLite.

La practica representa el mismo proceso que `proyecto_etl_vehiculos/etl.py`,
pero permite inspeccionar el flujo visualmente.

```text
SQLite vehicles + CSV market_prices
                 |
               Join
                 |
          Homologar / seleccionar
                 |
          Validar precios e IDs
             /             \
          pass           reject
            |               |
    vehicles_integrated  duckle_rejects.csv
```

## Alcance

Usar solo estos componentes:

- SQLite source
- CSV source
- Map o Join
- Filter
- SQLite sink
- CSV sink para rechazados

No usar en esta primera practica:

- conectores cloud
- APIs externas
- schedules
- dashboards
- pipelines paralelos

La meta es comprender Extract → Transform → Validate → Load.

## Preparacion

Desde esta carpeta del repositorio:

```bash
cd Clase04/proyecto_etl_vehiculos
python seed_database.py
```

Esto crea:

```text
data/vehicles.db
data/market_prices.csv
data/vehicle_specs.json
```

En Duckle, abre como workspace la carpeta:

```text
Clase04/proyecto_etl_vehiculos
```

Si Duckle aun no esta instalado, la documentacion del proyecto indica estas
alternativas:

```bash
pip install duckle
# o, sin instalarlo de forma permanente:
uvx duckle
```

En macOS Apple Silicon tambien puedes usar el binario de la release y abrirlo
con el procedimiento indicado por Duckle para Gatekeeper.

## Construccion en Duckle

### 1. Fuente SQLite

Agrega un componente **SQLite source**.

- Database/file: `data/vehicles.db`
- Table: `vehicles`
- Nombre sugerido: `vehicles_source`

Revisa el preview. Debe mostrar 10 vehiculos y las columnas:

```text
vehicle_id, brand, model, year, mileage
```

### 2. Fuente CSV

Agrega un componente **CSV source**.

- File: `data/market_prices.csv`
- Nombre sugerido: `market_prices_source`
- Activa autodeteccion de schema.

Revisa que `price` sea numerico y que existan los campos:

```text
vehicle_id, brand, model, price, source
```

### 3. Integracion

Agrega un componente **Map** o **Join** que permita usar una entrada
principal y una lookup.

- Entrada principal: `vehicles_source`
- Lookup: `market_prices_source`
- Relacion: `vehicle_id = vehicle_id`
- Tipo de relacion: left join si quieres observar tambien vehiculos sin precio;
  inner join si quieres conservar solo coincidencias.

Selecciona estas columnas de salida:

```text
vehicle_id
brand
model
year
mileage
price
source
```

Abre el **Plan** y explica el SQL generado. La idea no es memorizar la sintaxis:
es ver que una relacion visual se convierte en una consulta ejecutable.

### 4. Homologacion y regla de identidad

Antes de aceptar una fila, compara tambien marca y modelo. El `vehicle_id`
por si solo no garantiza que la informacion sea correcta.

Para esta practica usa estas reglas de equivalencia:

```text
VW             -> Volkswagen
VOLKSWAGEN     -> Volkswagen
NISSAN         -> Nissan
Nissan Motor   -> Nissan
```

En el editor visual puedes resolverlo con una expresion `CASE`, un Map o un
transform de reemplazo. La salida canonica debe ser:

```text
Volkswagen, Nissan, Toyota, Chevrolet, Mazda
```

La regla conceptual es:

```sql
lower(trim(brand_market)) = lower(trim(brand_db))
AND lower(trim(model_market)) = lower(trim(model_db))
```

### 5. Validacion y rejects

Agrega un **Filter** o validador con la rama principal `pass` y una rama
`reject`.

Regla minima para `pass`:

```sql
vehicle_id IS NOT NULL
AND price > 0
AND year BETWEEN 1990 AND 2026
```

Si ya agregaste la comparacion de identidad, incluyela tambien en la regla.

En la rama `reject`, conserva una columna `rejection_reason`. No borres las
filas invalidas: son evidencia para investigar la fuente.

Con los datos iniciales, espera aproximadamente:

```text
9 filas integradas
3 filas rechazadas
```

### 6. Crear variable derivada

En la rama `pass`, agrega:

```text
vehicle_age = 2026 - year
```

El dato integrado debe representar una fila por vehiculo. Si una fuente tiene
varias publicaciones del mismo vehiculo, agrega antes o despues del join:

```text
market_price  = promedio(price)
listings_count = count(price)
sources = fuentes distintas concatenadas
```

Para la primera corrida puedes conservar una fila por publicación y dejar la
agregacion como extensión.

### 7. Salidas

Agrega dos sinks:

**SQLite sink**

- Database: `data/vehicles.db`
- Table: `vehicles_integrated_duckle`
- Mode: overwrite

**CSV sink**

- File: `data/duckle_rejects.csv`
- Format: CSV
- Mode: overwrite

Usar `overwrite` en esta práctica hace que la ejecución sea repetible y evita
duplicar filas al ejecutar el pipeline dos veces.

## Verificacion

En Duckle revisa:

1. El preview de cada etapa.
2. Cuantas filas pasan y cuantas son rechazadas.
3. El SQL generado en Plan.
4. Que el sink SQLite se haya escrito.
5. Que la rama reject conserve las razones.

Después, desde la terminal:

```bash
python - <<'PY'
import sqlite3

with sqlite3.connect('data/vehicles.db') as conn:
    print(conn.execute(
        'SELECT COUNT(*) FROM vehicles_integrated_duckle'
    ).fetchone()[0])
PY
```

El conteo debe coincidir con las filas que viste en la rama `pass`.

## Actividad de extensión

Modificar el pipeline sin cambiar sus fuentes:

1. Agregar `data/vehicle_specs.json` como segunda lookup.
2. Integrar `city` y `category` por `vehicle_id`.
3. Rechazar vehículos sin especificaciones complementarias.
4. Guardar una tabla `vehicles_enriched_duckle`.
5. Comparar el resultado con `vehicles_integrated` producido por `etl.py`.

La pregunta de cierre es:

> ¿Qué ventajas ofrece ver el pipeline visualmente y qué decisiones siguen
> requiriendo entender los datos, aunque la herramienta genere el SQL?

## Qué debe entregar el estudiante

- Una captura o export del pipeline visual.
- El archivo de salida SQLite.
- El archivo de rechazos.
- Una nota corta con:
  - fuentes utilizadas;
  - regla de integración;
  - reglas de validación;
  - número de filas pass/reject;
  - qué ocurre al ejecutar dos veces.

## Relacion con Python

Duckle no reemplaza el concepto aprendido en Python:

| Duckle | `etl.py` |
|---|---|
| SQLite source | `pd.read_sql()` |
| CSV source | `pd.read_csv()` |
| Join/Map | `merge()` |
| Filter/validator | `validate()` |
| Reject sink | `etl_rejects` |
| SQLite sink | `to_sql()` |
| Run history | `etl_runs` |

La herramienta visualiza y ejecuta el flujo; el estudiante debe seguir siendo
capaz de explicar el contrato de entrada, la transformación y la validación.
