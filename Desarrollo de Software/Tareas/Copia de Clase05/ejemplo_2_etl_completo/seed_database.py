"""Crea data/vehicles.db con la tabla fuente `vehicles` (sistema origen)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "vehicles.db"

VEHICLES = [
    # vehicle_id, brand, model, year, mileage, mileage_unit, updated_at
    (1, "VW", "Golf", 2018, 45000, "km", "2026-08-10T09:00:00"),
    (2, "Nissan", "Versa", 2020, 28000, "km", "2026-08-12T10:30:00"),
    (3, "Toyota", "Corolla", 2019, 32000, "km", "2026-08-15T08:00:00"),
    (4, "Mazda", "3", 2021, 7500, "mi", "2026-08-16T11:00:00"),
    (5, "Honda", "Civic", 2017, 58000, "km", "2026-08-18T07:45:00"),
    (6, "VOLKSWAGEN", "Tiguan", 2016, 62000, "km", "2026-08-18T12:00:00"),
    (7, "nissan", "Sentra", 2022, 9000, "km", "2026-08-19T09:00:00"),
    (8, "Toyota", "Corolla", 2200, 12000, "km", "2026-08-19T09:30:00"),  # year invalido
    (9, "Honda", "Civic", 2015, -500, "km", "2026-08-20T10:00:00"),  # mileage invalido
    (10, "Kia", "Rio", 2019, 41000, "km", "2026-08-20T14:00:00"),  # marca sin info de fabricante
]


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE vehicles (
                vehicle_id INTEGER PRIMARY KEY,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage REAL NOT NULL,
                mileage_unit TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?)", VEHICLES
        )
        conn.commit()

    print(f"Sembrados {len(VEHICLES)} vehiculos en {DB_PATH}")


if __name__ == "__main__":
    main()
