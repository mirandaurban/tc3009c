"""Ejemplo 3 de ETL para la Clase 5: mismo proceso de ingenieria que el
ejemplo 2, pero con dos diferencias deliberadas para contrastar en clase:

1. Motor: DuckDB en vez de SQLite + pandas. Todo el EXTRACT/STAGE se hace
   con una sola sentencia SQL que lee el CSV directamente, y todo el
   TRANSFORM/INTEGRATE se hace con SQL dentro del motor analitico. Esto es
   un patron ELT (Extract -> Load crudo -> Transform con SQL), no un ETL
   clasico como el ejemplo 2 (Extract -> Transform en pandas -> Load).

2. Dataset: "Telco Customer Churn" (IBM), un dataset publico real, no
   sintetico. Trae DOS problemas de calidad de datos reales y no obvios,
   que son el caso interesante de esta clase:

   a) `TotalCharges` llega como texto (VARCHAR), no como numero. 11 filas
      tienen literalmente un espacio en blanco (' ') en vez de un valor.
      Esas 11 filas son, sin excepcion, clientes con tenure=0 (recien
      dados de alta, todavia no facturados). Es una regla de negocio, no
      un error: se corrige a 0.0. Cualquier fila con TotalCharges invalido
      y tenure != 0 si es un error real y va a cuarentena.

   b) Varias columnas categoricas (`MultipleLines`, `PaymentMethod`,
      `Contract`) traen valores envueltos en comillas simples literales
      dentro del dato, por ejemplo "'Electronic check'" en vez de
      "Electronic check". No es un problema de parsing de CSV: la comilla
      es parte del texto. Si no se limpia, un filtro o un JOIN por ese
      valor "funciona" (no lanza excepcion) pero no compara nunca lo que
      el analista cree que esta comparando -> exactamente el mensaje de
      la Slide 7: "sintacticamente correcto, semanticamente incorrecto".

Proceso (igual al de la Clase 5): DEFINE -> EXTRACT/STAGE -> VALIDATE
-> TRANSFORM -> INTEGRATE -> QUALITY GATE -> LOAD -> AUDIT.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


# ----------------------------------------------------------------------
# DEFINE: grain = un cliente (snapshot actual). El dataset fuente no trae
# un identificador de negocio, asi que se genera un customer_id sintetico
# en STAGE. Refresh = full load (es un snapshot, no hay updated_at):
# a diferencia del ejemplo 2 (incremental por watermark), aqui la
# idempotencia se logra reemplazando por completo la capa curated en
# cada corrida, no con UPSERT.
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ETLConfig:
    csv_path: Path
    database_path: Path
    curated_customers_parquet: Path
    curated_segments_parquet: Path
    quality_thresholds: dict[str, float]


def load_config() -> ETLConfig:
    return ETLConfig(
        csv_path=PROJECT_DIR / "data" / "telco_churn.csv",
        database_path=PROJECT_DIR / "data" / "telco.duckdb",
        curated_customers_parquet=PROJECT_DIR / "data" / "customers_curated.parquet",
        curated_segments_parquet=PROJECT_DIR / "data" / "churn_by_segment_curated.parquet",
        quality_thresholds={
            "completeness_min": 0.99,
            "quarantine_rate_max": 0.01,
            "churn_rate_min": 0.05,
            "churn_rate_max": 0.60,
        },
    )


# ----------------------------------------------------------------------
# EXTRACT + STAGE: en un motor OLAP como DuckDB, extraccion y staging
# suelen ser la misma sentencia: el CSV se carga tal cual (mismo texto
# crudo, sin homologar nada todavia) mas metadatos de procedencia.
# TotalCharges se fuerza a VARCHAR explicitamente para no depender de que
# el sniffer de tipos de DuckDB adivine correctamente: aqui se hace
# visible a proposito el problema de calidad de datos.
# ----------------------------------------------------------------------
def extract_and_stage(con: duckdb.DuckDBPyConnection, config: ETLConfig, batch_id: str) -> int:
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_customers AS
        SELECT
            row_number() OVER () AS customer_id,
            *,
            'csv:telco_churn' AS source_system,
            ? AS batch_id,
            current_timestamp AS ingested_at
        FROM read_csv_auto(?, header = true, types = {'TotalCharges': 'VARCHAR'})
        """,
        [batch_id, str(config.csv_path)],
    )
    row_count = con.execute("SELECT count(*) FROM stg_customers").fetchone()[0]
    logging.info("EXTRACT/STAGE: %s filas cargadas desde %s (batch_id=%s)", row_count, config.csv_path.name, batch_id)
    return row_count


# ----------------------------------------------------------------------
# VALIDATE: separa lo que es una regla de negocio conocida (TotalCharges
# en blanco cuando tenure=0) de lo que seria un error real (TotalCharges
# en blanco con tenure != 0, que en este dataset no ocurre pero se
# verifica explicitamente en vez de asumirlo).
# ----------------------------------------------------------------------
def validate(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    con.execute(
        """
        CREATE OR REPLACE TABLE etl_quarantine AS
        SELECT
            customer_id, batch_id, 'TotalCharges' AS field,
            'total_charges_blank_with_tenure_gt_0' AS rejection_reason
        FROM stg_customers
        WHERE trim(TotalCharges) = '' AND tenure <> 0

        UNION ALL

        SELECT
            customer_id, batch_id, 'MonthlyCharges' AS field,
            'monthly_charges_not_positive' AS rejection_reason
        FROM stg_customers
        WHERE MonthlyCharges IS NULL OR MonthlyCharges <= 0
        """
    )
    quarantined = con.execute("SELECT count(*) FROM etl_quarantine").fetchone()[0]

    con.execute(
        """
        CREATE OR REPLACE TABLE stg_customers_valid AS
        SELECT * FROM stg_customers
        WHERE customer_id NOT IN (SELECT customer_id FROM etl_quarantine)
        """
    )
    valid = con.execute("SELECT count(*) FROM stg_customers_valid").fetchone()[0]

    blank_but_new = con.execute(
        "SELECT count(*) FROM stg_customers WHERE trim(TotalCharges) = '' AND tenure = 0"
    ).fetchone()[0]

    logging.info(
        "VALIDATE: validos=%s quarantine=%s (de los cuales %s TotalCharges en blanco se explican "
        "por tenure=0 y se corrigen en TRANSFORM, no se descartan)",
        valid,
        quarantined,
        blank_but_new,
    )
    return valid, quarantined


# ----------------------------------------------------------------------
# TRANSFORM: todo con SQL dentro de DuckDB. Determinista: misma tabla de
# entrada + mismo SQL -> mismo resultado.
# ----------------------------------------------------------------------
def transform(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_customers_clean AS
        SELECT
            customer_id,
            gender,
            (SeniorCitizen = 1) AS senior_citizen,
            -- DuckDB infiere Partner/Dependents/Churn como BOOLEAN al leer el CSV
            -- (los unicos valores son 'Yes'/'No'), asi que se usan tal cual.
            Partner AS has_partner,
            Dependents AS has_dependents,
            tenure,
            CASE
                WHEN tenure BETWEEN 0 AND 12 THEN '0-12'
                WHEN tenure BETWEEN 13 AND 24 THEN '13-24'
                WHEN tenure BETWEEN 25 AND 48 THEN '25-48'
                ELSE '49+'
            END AS tenure_bucket,
            -- Limpieza de comillas simples literales embebidas en el dato
            -- (no es un problema de parsing de CSV, es texto sucio):
            trim(trim(MultipleLines, ''''), ' ') AS multiple_lines,
            trim(trim(PaymentMethod, ''''), ' ') AS payment_method,
            trim(trim(Contract, ''''), ' ') AS contract,
            InternetService AS internet_service,
            MonthlyCharges AS monthly_charges,
            -- Regla de negocio: blanco + tenure=0 -> 0.0 (aun no facturado).
            -- Cualquier otro caso invalido ya fue enviado a cuarentena en VALIDATE.
            CASE WHEN trim(TotalCharges) = '' THEN 0.0 ELSE CAST(TotalCharges AS DOUBLE) END AS total_charges,
            Churn AS churn_flag,
            batch_id,
            ingested_at
        FROM stg_customers_valid
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_customers_clean AS
        SELECT
            *,
            CASE WHEN tenure = 0 THEN monthly_charges ELSE total_charges / tenure END AS avg_monthly_spend
        FROM stg_customers_clean
        """
    )
    sample = con.execute(
        "SELECT payment_method, contract FROM stg_customers_clean LIMIT 1"
    ).fetchone()
    logging.info("TRANSFORM: comillas limpiadas, ejemplo payment_method=%r contract=%r", sample[0], sample[1])


# ----------------------------------------------------------------------
# INTEGRATE: aqui no se integran multiples fuentes (como en el ejemplo 2)
# sino dos GRAINS distintos para dos consumidores distintos: un Training
# Pipeline consume la tabla a nivel cliente, un dashboard de Analytics
# consume la tabla agregada por segmento.
# ----------------------------------------------------------------------
def integrate(con: duckdb.DuckDBPyConnection) -> dict:
    con.execute(
        """
        CREATE OR REPLACE TABLE churn_by_segment AS
        SELECT
            contract,
            tenure_bucket,
            count(*) AS customers,
            sum(CASE WHEN churn_flag THEN 1 ELSE 0 END) AS churned,
            round(avg(CASE WHEN churn_flag THEN 1.0 ELSE 0.0 END), 4) AS churn_rate,
            round(avg(avg_monthly_spend), 2) AS avg_monthly_spend
        FROM stg_customers_clean
        GROUP BY contract, tenure_bucket
        """
    )
    segments = con.execute("SELECT count(*) FROM churn_by_segment").fetchone()[0]
    overall_churn_rate = con.execute(
        "SELECT avg(CASE WHEN churn_flag THEN 1.0 ELSE 0.0 END) FROM stg_customers_clean"
    ).fetchone()[0]
    logging.info(
        "INTEGRATE: %s segmentos (contract x tenure_bucket) generados para Analytics | churn_rate global=%.4f",
        segments,
        overall_churn_rate,
    )
    return {"segments": segments, "overall_churn_rate": overall_churn_rate}


# ----------------------------------------------------------------------
# QUALITY GATE: no se carga solo porque el SQL no lanzo una excepcion.
# ----------------------------------------------------------------------
def quality_gate(
    con: duckdb.DuckDBPyConnection,
    source_rows: int,
    quarantined_rows: int,
    reconciliation: dict,
    thresholds: dict[str, float],
) -> dict:
    required = ["customer_id", "gender", "tenure", "contract", "monthly_charges", "total_charges"]
    completeness = con.execute(
        f"SELECT avg(CASE WHEN {' AND '.join(f'{c} IS NOT NULL' for c in required)} THEN 1.0 ELSE 0.0 END) "
        "FROM stg_customers_clean"
    ).fetchone()[0]
    quarantine_rate = quarantined_rows / source_rows if source_rows else 0.0
    churn_rate = reconciliation["overall_churn_rate"]

    metrics = {
        "completeness": round(completeness, 4),
        "quarantine_rate": round(quarantine_rate, 4),
        "churn_rate": round(churn_rate, 4),
    }
    failures = []
    if completeness < thresholds["completeness_min"]:
        failures.append("completeness")
    if quarantine_rate > thresholds["quarantine_rate_max"]:
        failures.append("quarantine_rate")
    if not (thresholds["churn_rate_min"] <= churn_rate <= thresholds["churn_rate_max"]):
        failures.append("churn_rate_out_of_expected_range")

    status = "FAIL" if failures else "PASS"
    logging.info("QUALITY GATE: status=%s metrics=%s", status, metrics)
    if failures:
        logging.error("QUALITY GATE: umbrales incumplidos: %s", failures)

    return {"status": status, "metrics": metrics, "failures": failures}


# ----------------------------------------------------------------------
# LOAD: full load idempotente (CREATE OR REPLACE) hacia la capa curated,
# mas exportacion a Parquet para simular una capa Lakehouse consumible
# sin abrir una conexion a la base de datos.
# ----------------------------------------------------------------------
def load(con: duckdb.DuckDBPyConnection, config: ETLConfig) -> int:
    con.execute(
        """
        CREATE OR REPLACE TABLE customers_curated AS
        SELECT * FROM stg_customers_clean
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE churn_by_segment_curated AS
        SELECT * FROM churn_by_segment
        """
    )
    con.execute(f"COPY customers_curated TO '{config.curated_customers_parquet}' (FORMAT PARQUET)")
    con.execute(f"COPY churn_by_segment_curated TO '{config.curated_segments_parquet}' (FORMAT PARQUET)")

    rows = con.execute("SELECT count(*) FROM customers_curated").fetchone()[0]
    logging.info(
        "LOAD: customers_curated=%s filas, churn_by_segment_curated exportadas a Parquet en %s",
        rows,
        config.curated_customers_parquet.name,
    )
    return rows


# ----------------------------------------------------------------------
# AUDIT: cada corrida deja evidencia, igual que en el ejemplo 2.
# ----------------------------------------------------------------------
def audit(
    con: duckdb.DuckDBPyConnection,
    run_id: str,
    started_at: str,
    finished_at: str,
    source_rows: int,
    valid_rows: int,
    quarantined_rows: int,
    curated_rows: int,
    status: str,
) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS etl_runs (
            run_id VARCHAR PRIMARY KEY,
            started_at VARCHAR, finished_at VARCHAR,
            source_rows INTEGER, valid_rows INTEGER,
            quarantined_rows INTEGER, curated_rows INTEGER,
            status VARCHAR
        )
        """
    )
    con.execute(
        """
        INSERT OR REPLACE INTO etl_runs
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [run_id, started_at, finished_at, source_rows, valid_rows, quarantined_rows, curated_rows, status],
    )
    logging.info("AUDIT: run_id=%s status=%s registrado en etl_runs", run_id, status)


def run() -> None:
    config = load_config()
    run_id = f"ETL_{uuid.uuid4().hex[:12]}"
    con = duckdb.connect(str(config.database_path))
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        source_rows = extract_and_stage(con, config, run_id)
        valid_rows, quarantined_rows = validate(con)
        transform(con)
        reconciliation = integrate(con)
        gate = quality_gate(con, source_rows, quarantined_rows, reconciliation, config.quality_thresholds)

        if gate["status"] == "FAIL":
            status = "FAILED_QUALITY_GATE"
            curated_rows = 0
        else:
            curated_rows = load(con, config)
            status = "SUCCESS"

        finished_at = datetime.now(timezone.utc).isoformat()
        audit(con, run_id, started_at, finished_at, source_rows, valid_rows, quarantined_rows, curated_rows, status)

        if status != "SUCCESS":
            raise SystemExit(f"Pipeline detenido: {status}")
    finally:
        con.close()


if __name__ == "__main__":
    run()
