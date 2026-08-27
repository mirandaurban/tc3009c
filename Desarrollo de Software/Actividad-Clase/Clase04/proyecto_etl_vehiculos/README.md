# Mini ETL de vehiculos

Este proyecto es el ejemplo practico de la Clase 4. Usa el caso de la
plataforma de vehiculos de la Clase 3, pero el objetivo ya no es entrenar un
modelo: es construir y operar un proceso reproducible de datos.

## Flujo

```text
SQLite + CSV + JSON
        |
      Extract
        |
     Transform
  homologacion + integracion + variables derivadas
        |
     Validate
  contrato + reglas + rechazos
        |
       Load
  SQLite: vehicles_integrated + etl_rejects + etl_runs
```

## Fuentes

- `data/vehicles.db`: tablas `vehicles`, `customers` y `sales`.
- `data/market_prices.csv`: precios externos por `vehicle_id`.
- `data/vehicle_specs.json`: ciudad y categoria complementarias.
- `data/brand_aliases.json`: reglas de homologacion (`VW` -> `Volkswagen`).
- `config.json`: rutas, tablas y fecha de corrida.

## Ejecucion desde cero

```bash
./run_etl.sh
```

El script:

1. recrea la base fuente con `seed_database.py`;
2. ejecuta `etl.py`;
3. consulta el resultado con `verify_etl.py`.

Para ejecutar solo el proceso sobre las fuentes existentes:

```bash
python etl.py
```

Para instalar dependencias:

```bash
pip install -r requirements.txt
```

## Salidas

### `vehicles_integrated`

Contiene el dato analitico integrado:

- `vehicle_id`
- `brand`, `model`
- `year`, `mileage`
- `vehicle_age`
- `city`, `category`
- `market_price`
- `listings_count`
- `sources`
- `etl_run_id`, `etl_run_date`

### `etl_rejects`

Conserva los registros que no entraron al dataset final y explica por que:

- `vehicle_id_not_found`
- `vehicle_identity_mismatch`
- `price_invalid`
- `year_out_of_range`
- `vehicle_specs_not_found`

### `etl_runs`

Registra una corrida completa: inicio, fin, filas leidas, integradas,
rechazadas y estado. Esto permite saber si el proceso corrio y cuanto produjo.

## Reglas importantes

- Un `JOIN` por `vehicle_id` no basta: se comparan tambien marca y modelo.
- `VW`, `VOLKSWAGEN` y `Nissan Motor` se homologan antes de comparar.
- Los precios no validos se rechazan, no se convierten silenciosamente.
- Las filas validas se agrupan por vehiculo para calcular precio promedio y
  cantidad de publicaciones.
- La carga usa reemplazo transaccional de las tablas de salida: ejecutar dos
  veces el mismo ETL no duplica registros.
- Si una etapa falla, el proceso termina con error y no registra la corrida como
  exitosa.

## Operacion

El log se escribe en `data/etl.log`. Para macOS/Linux se puede programar con
`cron`; en Windows, con Task Scheduler. Una entrada conceptual seria:

```cron
0 2 * * * /ruta/al/proyecto/run_etl.sh
```

Primero se debe probar el comando manualmente y usar rutas absolutas en el
scheduler.
