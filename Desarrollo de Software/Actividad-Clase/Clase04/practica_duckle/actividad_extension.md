# Extension: segunda fuente de lookup

Cuando la practica minima funcione, agrega `data/vehicle_specs.json`.

## Objetivo

Producir `vehicles_enriched_duckle` con:

```text
vehicle_id, brand, model, year, mileage, vehicle_age,
city, category, price, source
```

## Reglas

- Integrar por `vehicle_id`.
- Conservar solo vehiculos con especificaciones complementarias.
- Mantener la rama de rechazos.
- Usar overwrite.
- Ejecutar dos veces y comparar conteos.

## Preguntas

1. ¿La segunda lookup debe ser inner join o left join? ¿Por que?
2. ¿Que diferencia hay entre un rechazo de calidad y un registro sin match?
3. ¿Como conservarias varias publicaciones por vehiculo sin duplicar el
   registro final?
4. ¿Que parte del pipeline seria dificil de revisar si solo vieras el
   resultado final y no el Plan/Preview?
