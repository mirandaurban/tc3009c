-- Ejecutar despues de correr el pipeline en Duckle.

-- 1. Cuantas filas genero el sink.
SELECT COUNT(*) AS integrated_rows
FROM vehicles_integrated_duckle;

-- 2. Ver una muestra del resultado.
SELECT
    vehicle_id,
    brand,
    model,
    year,
    mileage,
    price,
    vehicle_age
FROM vehicles_integrated_duckle
ORDER BY vehicle_id
LIMIT 10;

-- 3. Resumen de precio por marca.
SELECT
    brand,
    AVG(price) AS average_market_price,
    COUNT(*) AS listings
FROM vehicles_integrated_duckle
GROUP BY brand
ORDER BY average_market_price DESC;

-- 4. Consultar rechazos producidos por el sink CSV desde Duckle.
-- El archivo se puede abrir como CSV source en una segunda corrida.
