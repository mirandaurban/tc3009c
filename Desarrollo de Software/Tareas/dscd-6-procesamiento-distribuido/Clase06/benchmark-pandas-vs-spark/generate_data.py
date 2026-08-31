"""
generate_data.py — genera data/vehicles.csv y data/manufacturers.csv
a la escala que se le indique, con el mismo esquema y la misma
distribución desigual entre marcas que ya se usa en la práctica de Spark
(útil para observar Data Skew).

Uso:
    python generate_data.py --rows 50000
    python generate_data.py --rows 50000000 --out-dir data

El número de filas es aproximado: se reparte proporcionalmente entre
las 10 marcas según los mismos pesos de la práctica, más 5 filas
inválidas a propósito (para ejercitar validación en el ETL).
"""
import argparse
import os
import random

BRANDS = ["Toyota", "Nissan", "BMW", "Mazda", "Volkswagen",
          "Ferrari", "Honda", "Chevrolet", "Hyundai", "Kia"]
WEIGHTS = [28, 22, 8, 10, 18, 1, 6, 4, 2, 1]

BASE_PRICE = {
    "Toyota": 320000, "Nissan": 260000, "BMW": 650000, "Mazda": 300000,
    "Volkswagen": 280000, "Ferrari": 3800000, "Honda": 290000,
    "Chevrolet": 270000, "Hyundai": 250000, "Kia": 240000,
}

MANUFACTURERS = [
    ("Toyota", "Japan", 1937), ("Nissan", "Japan", 1933), ("BMW", "Germany", 1916),
    ("Mazda", "Japan", 1920), ("Volkswagen", "Germany", 1937), ("Ferrari", "Italy", 1939),
    ("Honda", "Japan", 1948), ("Chevrolet", "USA", 1911), ("Hyundai", "South Korea", 1967),
    ("Kia", "South Korea", 1944),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=50_000,
                     help="Número aproximado de filas válidas a generar (default: 50,000)")
    ap.add_argument("--out-dir", default="data", help="Carpeta de salida (default: data)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    random.seed(args.seed)

    total_weight = sum(WEIGHTS)
    vehicles_path = os.path.join(args.out_dir, "vehicles.csv")
    vehicle_id = 1

    with open(vehicles_path, "w") as f:
        f.write("vehicle_id,brand,year,mileage,price\n")
        for brand, w in zip(BRANDS, WEIGHTS):
            n_brand = max(1, round(args.rows * w / total_weight))
            for _ in range(n_brand):
                year = random.randint(2015, 2024)
                mileage = random.randint(1000, 150000)
                price = int(BASE_PRICE[brand] * (1 - (2024 - year) * 0.05) * random.uniform(0.85, 1.15))
                price = max(price, 50000)
                f.write(f"{vehicle_id},{brand},{year},{mileage},{price}\n")
                vehicle_id += 1

        # 5 registros inválidos a propósito, igual que en la práctica.
        f.write(f"{vehicle_id},Toyota,2028,45000,320000\n"); vehicle_id += 1
        f.write(f"{vehicle_id},Nissan,2019,-500,180000\n"); vehicle_id += 1
        f.write(f"{vehicle_id},BMW,1985,60000,400000\n"); vehicle_id += 1
        f.write(f"{vehicle_id},Mazda,2021,50000,-100\n"); vehicle_id += 1
        f.write(f"{vehicle_id},Kia,2022,30000,0\n"); vehicle_id += 1

    manufacturers_path = os.path.join(args.out_dir, "manufacturers.csv")
    with open(manufacturers_path, "w") as f:
        f.write("brand,country,founded\n")
        for m in MANUFACTURERS:
            f.write(",".join(str(x) for x in m) + "\n")

    size_mb = os.path.getsize(vehicles_path) / (1024 * 1024)
    print(f"vehicles.csv: {vehicle_id - 1} filas, {size_mb:.1f} MB -> {vehicles_path}")
    print(f"manufacturers.csv: {len(MANUFACTURERS)} filas -> {manufacturers_path}")


if __name__ == "__main__":
    main()
