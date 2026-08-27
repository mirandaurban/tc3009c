from pathlib import Path

import pandas as pd

base_dir = Path(__file__).resolve().parent
actual_path = base_dir / "data" / "vehicle_listings_active.csv"
expected_path = base_dir / "data" / "vehicle_listings_active_expected.csv"

if not actual_path.exists():
    raise SystemExit(
        "No existe la salida. Ejecuta primero el pipeline inicial en Duckle."
    )

actual = pd.read_csv(actual_path).sort_values("vehicle_id").reset_index(drop=True)
expected = pd.read_csv(expected_path).sort_values("vehicle_id").reset_index(drop=True)

if not actual.equals(expected):
    raise SystemExit("La salida no coincide con la referencia esperada.")

print(f"OK: {len(actual)} filas activas coinciden con la salida esperada.")
