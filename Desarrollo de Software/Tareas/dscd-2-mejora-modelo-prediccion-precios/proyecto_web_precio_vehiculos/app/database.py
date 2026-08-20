import csv
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "price_predictions.csv"

FIELDNAMES = [
    "id",
    "created_at",
    "name",
    "fuel",
    "seats",
    "seller_type",
    "transmission",
    "owner",
    "year",
    "km_driven",
    "mileage",
    "engine",
    "max_power",
    "torque",
    "estimated_price",
    "model_version",
]

_lock = Lock() 

def init_db() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def _next_id() -> int:
    if not CSV_PATH.exists():
        return 1
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return 1
    return max(int(row["id"]) for row in rows) + 1


def save_prediction(features: dict, result: dict) -> None:
    init_db()
    with _lock:
        new_id = _next_id()
        row = {
            "id": new_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "name": features["name"],
            "fuel": features["fuel"],
            "seats": features["seats"],
            "seller_type": features["seller_type"],
            "transmission": features["transmission"],
            "owner": features["owner"],
            "year": features["year"],
            "km_driven": features["km_driven"],
            "mileage": features["mileage"],
            "engine": features["engine"],
            "max_power": features["max_power"],
            "torque": features["torque"],
            "estimated_price": result["estimated_price"],
            "model_version": result["model_version"],
        }
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(row)


def list_recent_predictions(limit: int = 20) -> list[dict]:
    init_db()
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    rows.sort(key=lambda r: int(r["id"]), reverse=True)
    rows = rows[:limit]

    for row in rows:
        row["id"] = int(row["id"])
        row["year"] = int(row["year"])
        row["km_driven"] = float(row["km_driven"])
        row["mileage"] = float(row["mileage"])
        row["engine"] = float(row["engine"])
        row["max_power"] = float(row["max_power"])
        row["torque"] = float(row["torque"])
        row["estimated_price"] = float(row["estimated_price"])

    return rows