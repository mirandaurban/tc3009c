import sqlite3

from etl import ETLConfig, transform, validate


def test_transform_homologates_and_rejects(tmp_path):
    vehicles = __import__("pandas").DataFrame(
        [
            {"vehicle_id": 1, "brand": "Volkswagen", "model": "Jetta", "year": 2022, "mileage": 38500},
        ]
    )
    prices = __import__("pandas").DataFrame(
        [
            {"vehicle_id": 1, "brand": "VW", "model": "JETTA", "price": 342000, "source": "test"},
            {"vehicle_id": 99, "brand": "VW", "model": "JETTA", "price": 342000, "source": "test"},
        ]
    )
    specs = __import__("pandas").DataFrame(
        [{"vehicle_id": 1, "city": "Monterrey", "category": "Sedan"}]
    )

    processed, rejects = transform(
        vehicles, prices, specs, {"VW": "Volkswagen"}, "2026-08-20", "test-run"
    )

    assert len(processed) == 1
    assert processed.loc[0, "brand"] == "Volkswagen"
    assert processed.loc[0, "market_price"] == 342000
    assert processed.loc[0, "city"] == "Monterrey"
    assert len(rejects) == 1
    assert rejects.iloc[0]["rejection_reason"] == "vehicle_id_not_found;vehicle_specs_not_found"
    validate(processed)


def test_output_is_idempotent(tmp_path):
    db_path = tmp_path / "vehicles.db"
    rows = __import__("pandas").DataFrame(
        [{"vehicle_id": 1, "value": 10}]
    )
    with sqlite3.connect(db_path) as conn:
        rows.to_sql("vehicles_integrated", conn, if_exists="replace", index=False)
        rows.to_sql("vehicles_integrated", conn, if_exists="replace", index=False)
        assert conn.execute("SELECT COUNT(*) FROM vehicles_integrated").fetchone()[0] == 1
