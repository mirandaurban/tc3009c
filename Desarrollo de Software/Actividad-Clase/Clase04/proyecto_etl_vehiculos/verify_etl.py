import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "vehicles.db"


with sqlite3.connect(DB_PATH) as conn:
    print("vehicles_integrated")
    for row in conn.execute(
        """
        SELECT vehicle_id, brand, model, year, mileage, market_price, listings_count
        FROM vehicles_integrated
        ORDER BY vehicle_id
        LIMIT 10
        """
    ):
        print(row)

    print("\netl_rejects")
    for row in conn.execute(
        "SELECT vehicle_id, rejection_reason FROM etl_rejects ORDER BY vehicle_id"
    ):
        print(row)
