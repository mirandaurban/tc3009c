# Ejemplo 3 — ETL con DuckDB sobre un dataset real (Telco Customer Churn)

Este ejemplo usa el mismo proceso de ingenieria de la clase (`DEFINE ->
EXTRACT/STAGE -> VALIDATE -> TRANSFORM -> INTEGRATE -> QUALITY GATE -> LOAD
-> AUDIT`), pero cambia dos cosas a proposito respecto al `ejemplo_2` para
que la comparacion sea explicita en clase:

- **Motor**: [DuckDB](https://duckdb.org/) en vez de SQLite + pandas. El
  EXTRACT y el STAGE son una sola sentencia SQL (`read_csv_auto`), y el
  TRANSFORM/INTEGRATE tambien se hacen con SQL dentro del motor. Es un
  patron **ELT** (se carga primero, se transforma despues dentro de la
  plataforma de datos), a diferencia del **ETL** clasico del ejemplo 2
  (se transforma en pandas antes de persistir).
- **Dataset**: [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
  (IBM), un dataset publico real (el mismo CSV usado en `Clase02`), no
  datos sinteticos generados para el ejercicio.

## El caso interesante: dos problemas de calidad de datos reales

### 1. `TotalCharges` llega como texto, no como numero

11 de las 7,043 filas tienen literalmente un espacio en blanco (`' '`) en
la columna `TotalCharges`. Un `CAST(TotalCharges AS DOUBLE)` directo falla.

Antes de "arreglarlo" hay que investigar **por que** pasa:

```sql
SELECT tenure, count(*) FROM stg_customers
WHERE trim(TotalCharges) = ''
GROUP BY tenure;
-- tenure = 0 en las 11 filas
```

Las 11 filas son, sin excepcion, clientes con `tenure = 0`: acaban de
darse de alta y todavia no se les ha facturado nada. **No es un error de
datos, es una regla de negocio**: `TotalCharges` deberia ser `0.0` para
esos clientes. Cualquier otra fila con `TotalCharges` invalido y
`tenure != 0` si es un error real, y en este ejemplo se manda a
cuarentena (`etl_quarantine`) en vez de "corregirse" a ciegas.

Es el mismo punto de la Slide 5 ("no generar una excepcion no significa
que los datos sean correctos") y de la Slide 8: una transformacion que
corrige datos debe basarse en una regla de negocio explicita y
documentada, no en un `fillna(0)` generico.

### 2. Columnas categoricas con comillas simples literales dentro del dato

`MultipleLines`, `PaymentMethod` y `Contract` traen valores como:

```text
'No phone service'
'Electronic check'
'One year'
```

Las comillas **son parte del texto**, no un artefacto de como Python o
DuckDB parsean el CSV. Si no se limpian:

```sql
SELECT * FROM stg_customers WHERE PaymentMethod = 'Electronic check';
-- 0 filas, aunque la columna "se ve" igual en un preview
```

La consulta no lanza ningun error. Simplemente nunca compara lo que el
analista cree que esta comparando. Es el mensaje central de la Slide 7:
**"Sintacticamente correcto, semanticamente incorrecto"**. La limpieza en
`TRANSFORM` usa `trim(x, '''')` para quitar la comilla y despues `trim`
para los espacios.

## Grain, refresh strategy e INTEGRATE

- El dataset fuente **no trae un identificador de negocio**. Se genera un
  `customer_id` sintetico (`row_number()`) en STAGE. Punto de discusion en
  clase: ¿que pasaria si dos corridas distintas del mismo CSV vinieran en
  distinto orden? El `customer_id` generado asi solo es estable dentro de
  una misma corrida sobre un snapshot fijo.
- **Refresh strategy = Full Load** (es un snapshot, no hay `updated_at`),
  a diferencia del `ejemplo_2` (incremental por watermark). La
  idempotencia se logra con `CREATE OR REPLACE TABLE`, no con `UPSERT`.
- `INTEGRATE` no combina multiples fuentes (como el ejemplo 2). Combina
  **dos grains distintos para dos consumidores distintos**:
  - `customers_curated`: grain = cliente. Lo consumiria un **Training
    Pipeline**.
  - `churn_by_segment_curated`: grain = segmento (`contract` x
    `tenure_bucket`). Lo consumiria un dashboard de **Analytics**.

## Instalación paso a paso (y qué hacer si algo falla)

DuckDB en Python es solo un paquete (`pip install duckdb`), no un
servidor que tengas que instalar aparte ni un programa con instalador. La
mayoría de los problemas al "levantarlo" no son de DuckDB en sí, sino del
entorno de Python de cada quien. Sigue estos pasos en orden y no te
saltes la verificación de cada uno.

### Paso 1 — Confirma qué Python vas a usar

```bash
python3 --version
```

Necesitas **Python 3.9 o superior**. Si el comando no existe o marca un
error, en Windows usa `py --version` en vez de `python3 --version`.

⚠️ **Si tienes Anaconda/Miniconda instalado**, es fácil terminar
instalando `duckdb` en un entorno y ejecutando el script con otro Python
distinto. Confirma primero cuál `python`/`pip` estás usando de verdad:

```bash
which python3   # macOS/Linux
where python     # Windows (cmd)
```

Si ves una ruta que contiene `anaconda3` o `miniconda3`, todo bien, pero
recuerda ese detalle: vas a tener que instalar `duckdb` en **ese mismo**
entorno, no en otro.

### Paso 2 — Crea un entorno virtual dedicado a esta práctica

No instales `duckdb` directo sobre tu Python del sistema. Crea un entorno
aislado dentro de la carpeta del ejercicio:

```bash
cd Clase05/ejemplo_3_etl_duckdb
python3 -m venv .venv
```

Actívalo:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (cmd.exe)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Tu prompt de terminal debe mostrar `(.venv)` al inicio de la línea. Si no
lo muestra, el entorno no se activó y vas a terminar instalando el
paquete en el lugar equivocado.

### Paso 3 — Instala las dependencias y verifica la importación

```bash
pip install --upgrade pip
pip install -r requirements.txt
python -c "import duckdb; print(duckdb.__version__)"
```

Si el último comando imprime un número de versión (por ejemplo `1.0.0`),
DuckDB está instalado y accesible desde ese Python. Si en cambio ves
`ModuleNotFoundError: No module named 'duckdb'`, **no** ejecutes
`etl_duckdb.py` todavía — ve a la sección de problemas abajo.

### Paso 4 — Corre el pipeline

```bash
./run_etl.sh
```

## Problemas comunes al instalar/ejecutar DuckDB y cómo resolverlos

### "ModuleNotFoundError: No module named 'duckdb'" al correr el script, aunque `pip install` dijo que sí se instaló

Es casi siempre un desajuste entre **dónde se instaló** el paquete y
**qué Python ejecuta** el script. Pasa mucho con VS Code: instalas en una
terminal con un entorno activado, pero el botón de "Run" o el kernel de
Jupyter usa otro intérprete.

- En VS Code: abre la paleta de comandos (`Cmd/Ctrl+Shift+P`) → **Python:
  Select Interpreter** → elige el que apunta a
  `Clase05/ejemplo_3_etl_duckdb/.venv/bin/python` (o `.venv\Scripts\python.exe`
  en Windows). Ese ícono también aparece abajo a la derecha de la ventana.
- En terminal: confirma con `which python` (o `where python`) que la ruta
  apunta dentro de `.venv`. Si no, vuelve a activar el entorno (Paso 2) en
  **esa misma terminal** antes de correr el script.
- Si usas un notebook de Jupyter: el kernel se selecciona aparte del
  intérprete de la terminal — revisa el selector de kernel en la esquina
  superior derecha del notebook.

### Error de SSL/certificados al hacer `pip install` (`SSLCertVerificationError`, `CERTIFICATE_VERIFY_FAILED`)

Común en redes de escuela, oficina o con antivirus/firewall corporativo
que inspecciona tráfico HTTPS.

- Primero, algo simple: reintenta con otra red (datos móviles, otra wifi)
  para confirmar si es la red la que bloquea.
- Si estás en Mac y acabas de instalar Python desde python.org (no
  Homebrew, no Anaconda), corre el instalador de certificados que viene
  con Python:

  ```bash
  open "/Applications/Python 3.x/Install Certificates.command"
  ```

- Como último recurso (no como primera opción, y avisa a tu profesor si
  lo necesitas), puedes decirle a pip que confíe en el índice de PyPI:

  ```bash
  pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org duckdb
  ```

### "ERROR: Could not find a version that satisfies the requirement duckdb" / "No matching distribution found"

Casi siempre es una de estas dos causas:

1. **Tu Python es demasiado nuevo o demasiado viejo** para la versión de
   DuckDB fijada en `requirements.txt`. Corre `python3 --version` y
   confirma que estás entre 3.9 y 3.13. Si tienes una versión mucho más
   nueva que acaba de salir, es normal que todavía no exista un paquete
   de DuckDB compilado para ella — instala una versión de Python un poco
   más antigua mientras el paquete se actualiza.
2. **No hay conexión a internet real** en el momento de instalar (estás
   en modo avión, en una red cautiva que pide iniciar sesión en el
   navegador antes de dar acceso, o detrás de un proxy que bloquea pip).
   Abre `https://pypi.org` en el navegador desde la misma red: si no
   carga, el problema es de red, no de Python.

### "Operation not permitted" / "Errno 1" al instalar paquetes

Esto pasa cuando intentas instalar sobre un Python del sistema protegido
(por ejemplo, el Python que viene con macOS, o una instalación de
Anaconda compartida entre varios usuarios) sin los permisos necesarios.
La solución **no** es usar `sudo pip install`. La solución es volver al
Paso 2 y trabajar siempre dentro de un entorno virtual (`.venv`), que es
tuyo y no requiere permisos especiales.

### El script corre pero imprime muchos `UserWarning` sobre `numexpr` o `bottleneck`

Son advertencias de `pandas` sobre versiones antiguas de librerías
auxiliares opcionales que trae tu instalación base de Anaconda. No
afectan el resultado del pipeline y puedes ignorarlas con seguridad —
no son errores de DuckDB ni de tu código.

### `pip install` se queda pegado sin avanzar por varios minutos

Antes de asumir que algo está mal, espera al menos 30 segundos: en redes
lentas, `pip` puede tardar en resolver la primera conexión. Si después de
un minuto sigue sin mostrar ningún progreso, cancela con `Ctrl+C` y
reintenta con:

```bash
pip install -v duckdb
```

El flag `-v` muestra qué está haciendo pip en cada momento y suele dejar
ver si el problema es de red, de resolución de dependencias, o de
permisos.

## Qué genera al correrlo

`run_etl.sh` corre el pipeline dos veces (para mostrar que el full load es
idempotente por reemplazo) y despues corre `verify_etl.py`.

Salidas en `data/`:

- `telco.duckdb`: base DuckDB con `stg_customers`, `etl_quarantine`,
  `customers_curated`, `churn_by_segment_curated` y `etl_runs` (auditoria).
- `customers_curated.parquet` y `churn_by_segment_curated.parquet`: la
  misma capa curated exportada a Parquet, para simular una capa Lakehouse
  consumible sin abrir una conexion a la base de datos.

Para explorar la base manualmente:

```bash
python -c "import duckdb; duckdb.connect('data/telco.duckdb').sql('SELECT * FROM churn_by_segment_curated ORDER BY churn_rate DESC').show()"
```
