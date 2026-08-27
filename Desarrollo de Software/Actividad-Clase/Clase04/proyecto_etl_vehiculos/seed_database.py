import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "vehicles.db"

VEHICLES = [
    (1, "Volkswagen", "Jetta", 2022, 38500),
    (2, "Nissan", "Sentra", 2021, 42000),
    (3, "Chevrolet", "Aveo", 2020, 68000),
    (4, "Volkswagen", "Jetta", 2020, 72000),
    (5, "Nissan", "Sentra", 2022, 31000),
    (6, "Toyota", "Corolla", 2021, 51000),
    (7, "Nissan", "Versa", 2020, 59000),
    (8, "Mazda", "CX-5", 2022, 28000),
    (9, "Chevrolet", "Aveo", 2019, 83000),
    (10, "Toyota", "Corolla", 2023, 19000),
]

CUSTOMERS = [
    (1, "Ana Lopez", "Monterrey"),
    (2, "Luis Garcia", "Guadalajara"),
    (3, "Sofia Martinez", "Ciudad de Mexico"),
]

SALES = [
    (1, 1, 1, "2026-01-15", 335000),
    (2, 3, 2, "2026-02-20", 220000),
    (3, 6, 3, "2026-03-11", 385000),
]


def seed_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            DROP TABLE IF EXISTS sales;
            DROP TABLE IF EXISTS customers;
            DROP TABLE IF EXISTS vehicles;

            CREATE TABLE vehicles (
                vehicle_id INTEGER PRIMARY KEY,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER NOT NULL
            );

            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL
            );

            CREATE TABLE sales (
                sale_id INTEGER PRIMARY KEY,
                vehicle_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                sale_price REAL NOT NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
            """
        )
        conn.executemany("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?)", VEHICLES)
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?)", CUSTOMERS)
        conn.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", SALES)

    print(f"SQLite listo: {DB_PATH}")
    print(f"vehicles: {len(VEHICLES)} | customers: {len(CUSTOMERS)} | sales: {len(SALES)}")


if __name__ == "__main__":
    seed_database()
