"""Ejemplo COMPLETO de ETL siguiendo el proceso usado en la Clase 5:

    DEFINE -> EXTRACT -> STAGE -> VALIDATE -> TRANSFORM -> INTEGRATE
           -> QUALITY GATE -> LOAD -> AUDIT

Caso: valuacion de vehiculos, con tres fuentes (SQLite, CSV, "API" simulada
via manufacturers.json) que se integran hacia `vehicles_curated`, la tabla
que consumirian despues un Training Pipeline y un Inference Pipeline.
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
MILES_TO_KM = 1.60934

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


# ----------------------------------------------------------------------
# DEFINE: contrato de configuracion del pipeline (source, destination,
# grain=vehiculo, business key=vehicle_id, refresh=incremental por watermark).
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ETLConfig:
    database_path: Path
    market_prices_path: Path
    manufacturers_path: Path
    aliases_path: Path
    watermark_path: Path
    output_table: str
    quarantine_table: str
    audit_table: str
    current_year: int
    allowed_currencies: set[str]
    quality_thresholds: dict[str, float]


def load_config() -> ETLConfig:
    with (PROJECT_DIR / "config.json").open(encoding="utf-8") as file:
        raw = json.load(file)
    return ETLConfig(
        database_path=PROJECT_DIR / raw["database_path"],
        market_prices_path=PROJECT_DIR / raw["market_prices_path"],
        manufacturers_path=PROJECT_DIR / raw["manufacturers_path"],
        aliases_path=PROJECT_DIR / raw["aliases_path"],
        watermark_path=PROJECT_DIR / raw["watermark_path"],
        output_table=raw["output_table"],
        quarantine_table=raw["quarantine_table"],
        audit_table=raw["audit_table"],
        current_year=raw["current_year"],
        allowed_currencies=set(raw["allowed_currencies"]),
        quality_thresholds=raw["quality_thresholds"],
    )


def read_watermark(path: Path) -> str:
    with path.open(encoding="utf-8") as file:
        return json.load(file)["last_processed_updated_at"]


def write_watermark(path: Path, value: str) -> None:
    path.write_text(json.dumps({"last_processed_updated_at": value}, indent=2), encoding="utf-8")


# ----------------------------------------------------------------------
# EXTRACT: cada fuente se lee de forma independiente. Los vehiculos se
# extraen de forma incremental usando el watermark; los fabricantes se
# consultan solo para marcas que aun no tenemos en la "cache" local.
# ----------------------------------------------------------------------
def extract(config: ETLConfig, watermark: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    with sqlite3.connect(config.database_path) as conn:
        vehicles = pd.read_sql(
            "SELECT * FROM vehicles WHERE updated_at > :watermark",
            conn,
            params={"watermark": watermark},
        )
    market_prices = pd.read_csv(config.market_prices_path)
    with config.manufacturers_path.open(encoding="utf-8") as file:
        manufacturers = json.load(file)

    logging.info(
        "EXTRACT: %s vehiculos nuevos/modificados desde watermark=%s | %s observaciones de precio",
        len(vehicles),
        watermark,
        len(market_prices),
    )
    return vehicles, market_prices, manufacturers


# ----------------------------------------------------------------------
# STAGE: se conserva evidencia de origen (source_system, batch_id,
# ingested_at) antes de aplicar cualquier regla de negocio.
# ----------------------------------------------------------------------
def stage(vehicles: pd.DataFrame, market_prices: pd.DataFrame, batch_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ingested_at = pd.Timestamp.now("UTC").isoformat()

    vehicles = vehicles.copy()
    vehicles["source_system"] = "sqlite:vehicles"
    vehicles["batch_id"] = batch_id
    vehicles["ingested_at"] = ingested_at

    market_prices = market_prices.copy()
    market_prices["source_system"] = "csv:market_prices"
    market_prices["batch_id"] = batch_id
    market_prices["ingested_at"] = ingested_at

    logging.info("STAGE: batch_id=%s asignado a ambas fuentes", batch_id)
    return vehicles, market_prices


# ----------------------------------------------------------------------
# VALIDATE: aplica el contrato de datos. Los registros invalidos van a
# cuarentena con su razon, no se descartan silenciosamente.
# ----------------------------------------------------------------------
def validate(
    staged_vehicles: pd.DataFrame,
    staged_prices: pd.DataFrame,
    config: ETLConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    v = staged_vehicles.copy()
    v_reasons = []
    for _, row in v.iterrows():
        reasons = []
        if pd.isna(row["vehicle_id"]):
            reasons.append("vehicle_id_null")
        if not (1990 <= row["year"] <= config.current_year):
            reasons.append("year_out_of_range")
        if row["mileage"] < 0:
            reasons.append("mileage_negative")
        v_reasons.append(";".join(reasons))
    v["rejection_reason"] = v_reasons
    quarantined_vehicles = v[v["rejection_reason"] != ""].copy()
    valid_vehicles = v[v["rejection_reason"] == ""].copy()

    p = staged_prices.copy()
    p_reasons = []
    for _, row in p.iterrows():
        reasons = []
        if pd.isna(row["price"]) or row["price"] <= 0:
            reasons.append("price_invalid")
        if row["currency"] not in config.allowed_currencies:
            reasons.append("currency_not_allowed")
        p_reasons.append(";".join(reasons))
    p["rejection_reason"] = p_reasons
    quarantined_prices = p[p["rejection_reason"] != ""].copy()
    valid_prices = p[p["rejection_reason"] == ""].copy()

    quarantine = pd.concat(
        [
            quarantined_vehicles.assign(source="vehicles")[
                ["source", "batch_id", "vehicle_id", "rejection_reason"]
            ],
            quarantined_prices.assign(source="market_prices")[
                ["source", "batch_id", "vehicle_id", "rejection_reason"]
            ],
        ],
        ignore_index=True,
    )

    logging.info(
        "VALIDATE: vehiculos validos=%s quarantine=%s | precios validos=%s quarantine=%s",
        len(valid_vehicles),
        len(quarantined_vehicles),
        len(valid_prices),
        len(quarantined_prices),
    )
    return valid_vehicles, valid_prices, quarantine


# ----------------------------------------------------------------------
# TRANSFORM: homologacion, conversion de unidades, variables derivadas.
# Deterministico: misma entrada + misma configuracion -> mismo resultado.
# ----------------------------------------------------------------------
def transform(
    valid_vehicles: pd.DataFrame,
    valid_prices: pd.DataFrame,
    aliases: dict,
    current_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    vehicles = valid_vehicles.copy()
    vehicles["brand"] = vehicles["brand"].str.strip().str.lower().map(aliases).fillna(vehicles["brand"])
    vehicles["model"] = vehicles["model"].astype(str).str.strip().str.title()

    is_miles = vehicles["mileage_unit"] == "mi"
    vehicles.loc[is_miles, "mileage"] = vehicles.loc[is_miles, "mileage"] * MILES_TO_KM
    vehicles["mileage_unit"] = "km"

    vehicles["vehicle_age"] = current_year - vehicles["year"]

    # Un vehiculo puede tener varias observaciones de precio (1:N):
    # se selecciona la mas reciente por vehicle_id.
    prices = valid_prices.copy()
    prices["observed_at"] = pd.to_datetime(prices["observed_at"])
    latest_idx = prices.groupby("vehicle_id")["observed_at"].idxmax()
    latest_prices = prices.loc[latest_idx, ["vehicle_id", "price", "currency", "observed_at"]]

    logging.info(
        "TRANSFORM: %s vehiculos transformados | %s precios mas recientes (de %s observaciones)",
        len(vehicles),
        len(latest_prices),
        len(prices),
    )
    return vehicles, latest_prices


# ----------------------------------------------------------------------
# INTEGRATE: combina vehiculos + ultimo precio + info de fabricante.
# Se valida la cardinalidad (1:1 esperado) mediante reconciliation.
# ----------------------------------------------------------------------
def integrate(
    vehicles: pd.DataFrame, latest_prices: pd.DataFrame, manufacturers: dict
) -> tuple[pd.DataFrame, dict]:
    rows_before = len(vehicles)
    merged = vehicles.merge(latest_prices, on="vehicle_id", how="left")

    if len(merged) != rows_before:
        raise ValueError(
            f"Cardinalidad inesperada en integrate: {rows_before} vehiculos -> {len(merged)} filas"
        )

    manufacturer_info = merged["brand"].map(
        lambda brand: manufacturers.get(brand, {"country": None, "segment": None})
    )
    merged["manufacturer_country"] = manufacturer_info.map(lambda info: info["country"])
    merged["manufacturer_segment"] = manufacturer_info.map(lambda info: info["segment"])

    reconciliation = {
        "rows_before": rows_before,
        "rows_after": len(merged),
        "matched_with_price": int(merged["price"].notna().sum()),
        "unmatched_price": int(merged["price"].isna().sum()),
        "duplicated_vehicle_id": int(merged["vehicle_id"].duplicated().sum()),
        "unknown_brand": int(merged["manufacturer_country"].isna().sum()),
    }
    logging.info("INTEGRATE / RECONCILIATION: %s", reconciliation)

    unknown_brands = sorted(set(merged.loc[merged["manufacturer_country"].isna(), "brand"]))
    for brand in unknown_brands:
        logging.warning("Marca sin informacion de fabricante en cache: se llamaria GET /manufacturers/%s", brand)

    return merged, reconciliation


# ----------------------------------------------------------------------
# QUALITY GATE: no se carga solo porque el proceso no lanzo una excepcion.
# ----------------------------------------------------------------------
def quality_gate(merged: pd.DataFrame, reconciliation: dict, thresholds: dict[str, float]) -> dict:
    total = reconciliation["rows_after"]
    if total == 0:
        logging.info("QUALITY GATE: sin filas nuevas que evaluar (no hay datos incrementales)")
        return {"status": "PASS", "metrics": {}}

    required = ["vehicle_id", "brand", "model", "year", "mileage"]
    completeness = merged[required].notna().all(axis=1).mean()
    duplicate_rate = reconciliation["duplicated_vehicle_id"] / total
    unmatched_rate = reconciliation["unmatched_price"] / total
    unknown_brand_rate = reconciliation["unknown_brand"] / total

    metrics = {
        "completeness": round(completeness, 4),
        "duplicate_rate": round(duplicate_rate, 4),
        "unmatched_rate": round(unmatched_rate, 4),
        "unknown_brand_rate": round(unknown_brand_rate, 4),
    }
    failures = []
    if completeness < thresholds["completeness_min"]:
        failures.append("completeness")
    if duplicate_rate > thresholds["duplicate_rate_max"]:
        failures.append("duplicate_rate")
    if unmatched_rate > thresholds["unmatched_rate_max"]:
        failures.append("unmatched_rate")
    if unknown_brand_rate > thresholds["unknown_brand_rate_max"]:
        failures.append("unknown_brand_rate")

    status = "FAIL" if failures else "PASS"
    logging.info("QUALITY GATE: status=%s metrics=%s", status, metrics)
    if failures:
        logging.error("QUALITY GATE: umbrales incumplidos: %s", failures)

    return {"status": status, "metrics": metrics, "failures": failures}


# ----------------------------------------------------------------------
# LOAD: UPSERT idempotente dentro de una transaccion. Repetir el mismo
# batch no debe duplicar ni acumular filas en vehicles_curated.
# ----------------------------------------------------------------------
def load(config: ETLConfig, merged: pd.DataFrame, quarantine: pd.DataFrame, batch_id: str) -> tuple[int, int]:
    inserted = 0
    updated = 0
    with sqlite3.connect(config.database_path) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {config.output_table} (
                vehicle_id INTEGER PRIMARY KEY,
                brand TEXT, model TEXT, year INTEGER,
                mileage REAL, vehicle_age INTEGER,
                price REAL, currency TEXT,
                manufacturer_country TEXT, manufacturer_segment TEXT,
                batch_id TEXT, updated_at TEXT
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {config.quarantine_table} (
                source TEXT, batch_id TEXT, vehicle_id INTEGER, rejection_reason TEXT
            )
            """
        )
        try:
            with conn:
                for _, row in merged.iterrows():
                    cur = conn.execute(
                        f"SELECT 1 FROM {config.output_table} WHERE vehicle_id = ?", (row["vehicle_id"],)
                    )
                    exists = cur.fetchone() is not None
                    conn.execute(
                        f"""
                        INSERT INTO {config.output_table}
                        (vehicle_id, brand, model, year, mileage, vehicle_age, price, currency,
                         manufacturer_country, manufacturer_segment, batch_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(vehicle_id) DO UPDATE SET
                            brand=excluded.brand, model=excluded.model, year=excluded.year,
                            mileage=excluded.mileage, vehicle_age=excluded.vehicle_age,
                            price=excluded.price, currency=excluded.currency,
                            manufacturer_country=excluded.manufacturer_country,
                            manufacturer_segment=excluded.manufacturer_segment,
                            batch_id=excluded.batch_id, updated_at=excluded.updated_at
                        """,
                        (
                            int(row["vehicle_id"]), row["brand"], row["model"], int(row["year"]),
                            float(row["mileage"]), int(row["vehicle_age"]),
                            None if pd.isna(row["price"]) else float(row["price"]),
                            row.get("currency") if pd.notna(row.get("currency")) else None,
                            row["manufacturer_country"], row["manufacturer_segment"],
                            batch_id, row["ingested_at"],
                        ),
                    )
                    updated += 1 if exists else 0
                    inserted += 0 if exists else 1

                if len(quarantine) > 0:
                    quarantine.to_sql(config.quarantine_table, conn, if_exists="append", index=False)
        except Exception:
            logging.error("LOAD: error durante la transaccion, se hace ROLLBACK")
            raise

    logging.info("LOAD: %s insertados, %s actualizados (UPSERT) en %s", inserted, updated, config.output_table)
    return inserted, updated


# ----------------------------------------------------------------------
# AUDIT: cada corrida deja evidencia de lo que ocurrio.
# ----------------------------------------------------------------------
def audit(
    config: ETLConfig,
    run_id: str,
    started_at: str,
    finished_at: str,
    watermark_before: str,
    watermark_after: str,
    counts: dict,
    status: str,
) -> None:
    with sqlite3.connect(config.database_path) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {config.audit_table} (
                run_id TEXT PRIMARY KEY,
                started_at TEXT, finished_at TEXT,
                watermark_before TEXT, watermark_after TEXT,
                source_vehicles INTEGER, valid_vehicles INTEGER, quarantined_vehicles INTEGER,
                inserted INTEGER, updated INTEGER,
                status TEXT
            )
            """
        )
        with conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {config.audit_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id, started_at, finished_at, watermark_before, watermark_after,
                    counts["source_vehicles"], counts["valid_vehicles"], counts["quarantined_vehicles"],
                    counts["inserted"], counts["updated"], status,
                ),
            )
    logging.info("AUDIT: run_id=%s status=%s registrado en %s", run_id, status, config.audit_table)


def main() -> None:
    config = load_config()
    run_id = str(uuid.uuid4())
    batch_id = f"ETL_{pd.Timestamp.now('UTC').strftime('%Y%m%d_%H%M%S')}"
    started_at = pd.Timestamp.now("UTC").isoformat()
    watermark_before = read_watermark(config.watermark_path)

    logging.info("=== ETL COMPLETO iniciado | run_id=%s batch_id=%s ===", run_id, batch_id)

    vehicles, market_prices, manufacturers = extract(config, watermark_before)

    if vehicles.empty:
        logging.info("Sin vehiculos nuevos desde el watermark: se registra corrida vacia (incremental correcto)")
        finished_at = pd.Timestamp.now("UTC").isoformat()
        audit(
            config, run_id, started_at, finished_at, watermark_before, watermark_before,
            {"source_vehicles": 0, "valid_vehicles": 0, "quarantined_vehicles": 0, "inserted": 0, "updated": 0},
            "SUCCESS",
        )
        return

    with config.aliases_path.open(encoding="utf-8") as file:
        aliases = json.load(file)

    staged_vehicles, staged_prices = stage(vehicles, market_prices, batch_id)
    valid_vehicles, valid_prices, quarantine = validate(staged_vehicles, staged_prices, config)

    if valid_vehicles.empty:
        logging.warning("Todos los vehiculos del batch fueron a cuarentena: no hay nada que cargar")
        finished_at = pd.Timestamp.now("UTC").isoformat()
        audit(
            config, run_id, started_at, finished_at, watermark_before, watermark_before,
            {
                "source_vehicles": len(vehicles), "valid_vehicles": 0,
                "quarantined_vehicles": len(quarantine), "inserted": 0, "updated": 0,
            },
            "SUCCESS_EMPTY",
        )
        return

    transformed_vehicles, latest_prices = transform(valid_vehicles, valid_prices, aliases, config.current_year)
    merged, reconciliation = integrate(transformed_vehicles, latest_prices, manufacturers)
    gate_result = quality_gate(merged, reconciliation, config.quality_thresholds)

    if gate_result["status"] == "FAIL":
        finished_at = pd.Timestamp.now("UTC").isoformat()
        audit(
            config, run_id, started_at, finished_at, watermark_before, watermark_before,
            {
                "source_vehicles": len(vehicles), "valid_vehicles": len(valid_vehicles),
                "quarantined_vehicles": len(quarantine), "inserted": 0, "updated": 0,
            },
            "FAILED_QUALITY_GATE",
        )
        raise SystemExit("Pipeline detenido: la calidad de los datos no cumple los umbrales definidos")

    inserted, updated = load(config, merged, quarantine, batch_id)

    watermark_after = str(staged_vehicles["updated_at"].max())
    write_watermark(config.watermark_path, watermark_after)

    finished_at = pd.Timestamp.now("UTC").isoformat()
    audit(
        config, run_id, started_at, finished_at, watermark_before, watermark_after,
        {
            "source_vehicles": len(vehicles), "valid_vehicles": len(valid_vehicles),
            "quarantined_vehicles": len(quarantine), "inserted": inserted, "updated": updated,
        },
        "SUCCESS",
    )
    logging.info("=== ETL COMPLETO finalizado: watermark %s -> %s ===", watermark_before, watermark_after)


if __name__ == "__main__":
    main()
