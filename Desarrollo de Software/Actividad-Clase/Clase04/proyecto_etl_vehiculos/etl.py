import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ETLConfig:
    database_path: Path
    market_prices_path: Path
    vehicle_specs_path: Path
    aliases_path: Path
    output_table: str
    rejects_table: str
    log_path: Path
    run_date: str


VEHICLE_COLUMNS = {"vehicle_id", "brand", "model", "year", "mileage"}
MARKET_COLUMNS = {"vehicle_id", "brand", "model", "price", "source"}
SPEC_COLUMNS = {"vehicle_id", "city", "category"}


def load_config() -> ETLConfig:
    with (PROJECT_DIR / "config.json").open(encoding="utf-8") as file:
        raw = json.load(file)

    return ETLConfig(
        database_path=PROJECT_DIR / raw["database_path"],
        market_prices_path=PROJECT_DIR / raw["market_prices_path"],
        vehicle_specs_path=PROJECT_DIR / raw["vehicle_specs_path"],
        aliases_path=PROJECT_DIR / "data" / "brand_aliases.json",
        output_table=raw["output_table"],
        rejects_table=raw["rejects_table"],
        log_path=PROJECT_DIR / raw["log_path"],
        run_date=raw["run_date"],
    )


def configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")],
        force=True,
    )


def _require_columns(frame: pd.DataFrame, required: set[str], source: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{source} is missing columns: {sorted(missing)}")


def extract(
    config: ETLConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str]]:
    with sqlite3.connect(config.database_path) as conn:
        vehicles = pd.read_sql(
            "SELECT vehicle_id, brand, model, year, mileage FROM vehicles", conn
        )

    market_prices = pd.read_csv(config.market_prices_path)
    with config.vehicle_specs_path.open(encoding="utf-8") as file:
        vehicle_specs = pd.DataFrame(json.load(file))
    with config.aliases_path.open(encoding="utf-8") as file:
        aliases = json.load(file)

    _require_columns(vehicles, VEHICLE_COLUMNS, "SQLite vehicles")
    _require_columns(market_prices, MARKET_COLUMNS, "market_prices.csv")
    _require_columns(vehicle_specs, SPEC_COLUMNS, "vehicle_specs.json")

    logging.info("SQLite: %s records", len(vehicles))
    logging.info("CSV: %s records", len(market_prices))
    logging.info("JSON specs: %s records", len(vehicle_specs))
    logging.info("JSON aliases: %s rules", len(aliases))
    return vehicles, market_prices, vehicle_specs, aliases


def transform(
    vehicles: pd.DataFrame,
    market_prices: pd.DataFrame,
    vehicle_specs: pd.DataFrame,
    aliases: dict[str, str],
    run_date: str,
    run_id: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_id = run_id or str(uuid.uuid4())
    prices = market_prices.copy()
    prices["brand_original"] = prices["brand"]
    prices["brand"] = prices["brand"].replace(aliases)
    prices["brand"] = prices["brand"].astype("string").str.strip()
    prices["model"] = prices["model"].astype("string").str.strip().str.title()
    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")

    specs = vehicle_specs.copy()
    specs["city"] = specs["city"].astype("string").str.strip()
    specs["category"] = specs["category"].astype("string").str.strip()

    integrated = prices.merge(
        vehicles,
        on="vehicle_id",
        how="left",
        suffixes=("_market", "_db"),
        indicator=True,
    )
    integrated = integrated.merge(specs, on="vehicle_id", how="left", indicator="_spec_merge")

    rejection_reasons = []
    for _, row in integrated.iterrows():
        reasons = []
        if row["_merge"] != "both":
            reasons.append("vehicle_id_not_found")
        elif (
            str(row["brand_market"]).casefold().strip()
            != str(row["brand_db"]).casefold().strip()
            or str(row["model_market"]).casefold().strip()
            != str(row["model_db"]).casefold().strip()
        ):
            reasons.append("vehicle_identity_mismatch")
        if row["_spec_merge"] != "both":
            reasons.append("vehicle_specs_not_found")
        if pd.isna(row["price"]) or row["price"] <= 0:
            reasons.append("price_invalid")
        if not pd.isna(row.get("year")) and not 1990 <= row["year"] <= 2026:
            reasons.append("year_out_of_range")
        rejection_reasons.append(";".join(reasons))

    integrated["rejection_reason"] = rejection_reasons
    rejects = integrated[integrated["rejection_reason"] != ""].copy()
    valid = integrated[integrated["rejection_reason"] == ""].copy()

    valid["vehicle_age"] = 2026 - valid["year"].astype(int)
    valid = (
        valid.groupby(
            [
                "vehicle_id",
                "brand_db",
                "model_db",
                "year",
                "mileage",
                "vehicle_age",
                "city",
                "category",
            ],
            as_index=False,
        )
        .agg(
            market_price=("price", "mean"),
            listings_count=("price", "count"),
            sources=("source", lambda values: ",".join(sorted(set(values)))),
        )
    )
    valid["etl_run_id"] = run_id
    valid["etl_run_date"] = run_date
    valid = valid.rename(
        columns={
            "brand_db": "brand",
            "model_db": "model",
            "mileage": "mileage",
        }
    )
    valid = valid[
        [
            "vehicle_id",
            "brand",
            "model",
            "year",
            "mileage",
            "vehicle_age",
            "city",
            "category",
            "market_price",
            "listings_count",
            "sources",
            "etl_run_id",
            "etl_run_date",
        ]
    ]

    rejects["etl_run_date"] = run_date
    rejects["etl_run_id"] = run_id
    logging.info("Integrated: %s records", len(valid))
    logging.info("Rejected: %s records", len(rejects))
    return valid, rejects


def validate(processed: pd.DataFrame) -> None:
    required_columns = {
        "vehicle_id",
        "brand",
        "model",
        "year",
        "mileage",
        "vehicle_age",
        "city",
        "category",
        "market_price",
        "listings_count",
        "sources",
        "etl_run_id",
        "etl_run_date",
    }
    missing = required_columns.difference(processed.columns)
    if missing:
        raise ValueError(f"Missing output columns: {sorted(missing)}")
    if processed["vehicle_id"].isna().any():
        raise ValueError("vehicle_id contains null values")
    if processed["market_price"].isna().any() or (processed["market_price"] <= 0).any():
        raise ValueError("market_price contains invalid values")
    if ((processed["year"] < 1990) | (processed["year"] > 2026)).any():
        raise ValueError("year contains values outside the accepted range")
    if processed["vehicle_id"].duplicated().any():
        raise ValueError("vehicle_id is not unique in the integrated output")
    if processed["city"].isna().any() or processed["category"].isna().any():
        raise ValueError("Complementary vehicle specs contain null values")
    logging.info("Validation passed: %s records", len(processed))


def load(
    config: ETLConfig,
    processed: pd.DataFrame,
    rejects: pd.DataFrame,
    run_id: str,
    started_at: str,
    finished_at: str,
) -> None:
    with sqlite3.connect(config.database_path) as conn:
        with conn:
            processed.to_sql(config.output_table, conn, if_exists="replace", index=False)
            rejects.to_sql(config.rejects_table, conn, if_exists="replace", index=False)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS etl_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    source_vehicles INTEGER NOT NULL,
                    source_market_prices INTEGER NOT NULL,
                    source_specs INTEGER NOT NULL,
                    integrated_rows INTEGER NOT NULL,
                    rejected_rows INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO etl_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    started_at,
                    finished_at,
                    int(processed.attrs.get("source_vehicles", 0)),
                    int(processed.attrs.get("source_market_prices", 0)),
                    int(processed.attrs.get("source_specs", 0)),
                    len(processed),
                    len(rejects),
                    "success",
                ),
            )
    logging.info("Load completed: %s, %s and etl_runs", config.output_table, config.rejects_table)


def main() -> None:
    config = load_config()
    configure_logging(config.log_path)
    run_id = str(uuid.uuid4())
    started_at = pd.Timestamp.now("UTC").isoformat()
    logging.info("ETL started")
    vehicles, market_prices, vehicle_specs, aliases = extract(config)
    processed, rejects = transform(
        vehicles, market_prices, vehicle_specs, aliases, config.run_date, run_id
    )
    processed.attrs.update(
        source_vehicles=len(vehicles),
        source_market_prices=len(market_prices),
        source_specs=len(vehicle_specs),
    )
    validate(processed)
    finished_at = pd.Timestamp.now("UTC").isoformat()
    load(config, processed, rejects, run_id, started_at, finished_at)
    logging.info("ETL finished")


if __name__ == "__main__":
    main()
