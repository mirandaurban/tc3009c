# Ejemplo 1 — ETL básico

Un solo archivo (`etl_basico.py`) con el patrón mínimo `Extract -> Transform
-> Load` sobre un CSV de vehículos con datos sucios (marcas escritas de
distintas formas, precios negativos o en cero, kilometraje faltante, un año
inválido).

## Ejecutar

```bash
./run_etl.sh
```

El script instala `pandas` si hace falta, corre `etl_basico.py` y muestra el
resultado. Esto genera `data/vehiculos_clean.csv`.

## Qué hace

1. **Extract**: lee `data/vehiculos_raw.csv` completo.
2. **Transform**: homologa marca, normaliza el modelo, filtra registros
   inválidos (precio, kilometraje, año) y calcula `vehicle_age`.
3. **Load**: sobrescribe `data/vehiculos_clean.csv` con el resultado.

## Qué le falta a propósito (para discutir en clase)

- No hay capa de staging: el dato crudo rechazado no se conserva en ningún
  lado, así que no podemos saber después *qué* se descartó ni *por qué*.
- No hay `batch_id` ni fecha de ejecución: si el archivo cambia entre
  corridas, no hay forma de rastrear qué corrida produjo qué fila.
- No hay contrato de datos explícito: las reglas de validez están
  hardcodeadas dentro de `transform()`, mezcladas con la lógica de limpieza.
- No hay tabla ni archivo de auditoría: no sabemos cuántos registros entraron,
  cuántos se rechazaron, ni si la corrida "tuvo éxito" más allá de no lanzar
  una excepción.
- La carga reemplaza el archivo completo cada vez: funciona aquí porque es
  `Full Load`, pero no sería una estrategia válida para una carga
  incremental sin control de duplicados.

Comparar esta lista con lo implementado en `ejemplo_2_etl_completo/` es el
punto central del ejercicio.
