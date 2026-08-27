# Práctica 0 — Primera ejecución con Duckle

## Para qué sirve este ejemplo

Antes de integrar SQLite, CSV y reglas de calidad, necesitamos entender qué
hace Duckle en una ejecución básica.

Duckle permite construir un flujo de datos como un grafo:

```text
Fuente → Transformación → Destino
```

En esta práctica:

```text
CSV de publicaciones → Filter status = active → CSV de salida
```

No hay joins, APIs, modelos ni bases de datos todavía. El propósito es aislar
la idea de una tubería ETL y observar qué ocurre al ejecutarla.

## Qué va a aprender el estudiante

Al terminar esta práctica podrá explicar:

- qué es una fuente;
- qué es una transformación;
- qué es un destino o sink;
- cómo se conectan los nodos;
- qué significa ejecutar una corrida;
- cómo revisar filas de entrada y salida;
- por qué una salida `overwrite` puede hacer repetible el proceso.

## Preparar el workspace

Abre en Duckle esta carpeta:

```text
Clase04/practica_duckle
```

El archivo de entrada ya está preparado en:

```text
data/vehicle_listings_demo.csv
```

Si aún no tienes Duckle:

```bash
pip install duckle
```

O ejecútalo de forma temporal con:

```bash
uvx duckle
```

En el primer arranque, instala DuckDB cuando Duckle lo solicite.

## Construir el pipeline

### 1. Agregar la fuente

En el panel de componentes, agrega una fuente **CSV**.

Configura:

```text
Path: data/vehicle_listings_demo.csv
```

Activa **Autodetect schema** y abre **Preview**.

Debes observar 6 filas y estas columnas:

```text
vehicle_id, brand, model, year, price, status
```

Explicación:

> Este nodo no transforma los datos. Solo los pone a disposición del pipeline.

### 2. Agregar el filtro

Agrega un transform **Filter** y conecta:

```text
CSV source → Filter
```

Usa esta condición:

```sql
status = 'active'
```

Explicación:

> El filtro recibe filas y deja pasar únicamente las que cumplen una regla.

El preview del filtro debe mostrar 4 filas.

### 3. Agregar la salida

Agrega un sink **CSV** y conecta:

```text
Filter pass → CSV sink
```

Configura:

```text
Path: data/vehicle_listings_active.csv
Mode: overwrite
```

No conectes todavía la salida `reject`: en este primer ejemplo no estamos
rechazando datos, solamente filtrando filas que no necesitamos.

### 4. Ejecutar

Presiona **Run**.

Observa:

1. el orden de ejecución;
2. cuántas filas lee la fuente;
3. cuántas filas deja pasar el filtro;
4. dónde se escribió el CSV;
5. el preview del sink;
6. el **Plan** o SQL generado.

Resultado esperado:

```text
Entrada: 6 filas
Filtro: status = active
Salida: 4 filas
Destino: data/vehicle_listings_active.csv
```

El archivo esperado está guardado como referencia en:

```text
data/vehicle_listings_active_expected.csv
```

## Cómo funciona Duckle en este ejemplo

Duckle interpreta el grafo y lo ejecuta con DuckDB. Conceptualmente, el flujo
se parece a:

```sql
COPY (
    SELECT *
    FROM read_csv_auto('data/vehicle_listings_demo.csv')
    WHERE status = 'active'
) TO 'data/vehicle_listings_active.csv' (HEADER, OVERWRITE);
```

La interfaz visual no elimina el SQL: lo genera y permite inspeccionarlo.

El estudiante no debe memorizar este SQL. Debe identificar la correspondencia:

| Concepto | En Duckle | En SQL |
|---|---|---|
| Fuente | CSV source | `read_csv_auto(...)` |
| Transformación | Filter | `WHERE` |
| Destino | CSV sink | `COPY (...) TO ...` |
| Repetibilidad | overwrite | reemplazar la salida |

## Segunda ejecución

Presiona **Run** otra vez.

El resultado debe seguir teniendo 4 filas, no 8. Esto introduce la idea de
idempotencia básica: repetir la corrida no duplica el archivo de salida cuando
el modo es `overwrite`.

## Preguntas rápidas

- ¿Qué cambiaría si el filtro fuera `status = 'sold'`?
- ¿Qué pasaría si conectamos el sink a la entrada original en lugar de al
  puerto `pass` del filtro?
- ¿Qué diferencia hay entre ver una fila en Preview y validarla?
- ¿Qué información registrarías en un log de esta corrida?

## Puente hacia la práctica de vehículos

Ahora sustituimos el ejemplo simple:

```text
CSV → Filter → CSV
```

por el problema real de la clase:

```text
SQLite vehicles + CSV market_prices
                 ↓
              Join / Map
                 ↓
       Homologar y validar
             /         \
          pass       reject
            |           |
   SQLite integrado   CSV rechazos
```

La idea nueva no es aprender más botones. Es reconocer que el pipeline creció
porque el problema de datos creció.
