import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "price_predictions.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                anio INTEGER NOT NULL,
                km INTEGER NOT NULL,
                transmision TEXT NOT NULL,
                estimated_price REAL NOT NULL,
                model_version TEXT NOT NULL
            )
            """
        )


def save_prediction(features: dict, result: dict) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO price_predictions (
                marca,
                modelo,
                anio,
                km,
                transmision,
                estimated_price,
                model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                features["marca"],
                features["modelo"],
                features["anio"],
                features["km"],
                features["transmision"],
                result["estimated_price"],
                result["model_version"],
            ),
        )


def list_recent_predictions(limit: int = 20) -> list[dict]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                marca,
                modelo,
                anio,
                km,
                transmision,
                estimated_price,
                model_version
            FROM price_predictions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]
