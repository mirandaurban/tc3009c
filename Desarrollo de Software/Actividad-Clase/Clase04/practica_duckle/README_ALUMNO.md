# Guia docente breve

## Intencion

Duckle se usa como una primera visualizacion del concepto ETL. La practica no
pretende enseñar toda la herramienta.

## Secuencia sugerida: 20 minutos

### Primera ejecucion: 8 minutos

1. Abrir `README_INICIAL.md`.
2. Mostrar `vehicle_listings_demo.csv` y preguntar que significa cada fila.
3. Crear CSV source, Filter (`status = 'active'`) y CSV sink.
4. Ejecutar y observar `6 → 4` filas.
5. Abrir Plan/SQL y explicar la correspondencia con `WHERE` y `COPY`.
6. Ejecutar de nuevo para introducir `overwrite` e idempotencia.

### Caso ETL: 12 minutos

7. Mostrar las dos fuentes y preguntar por que no basta con concatenarlas.
8. Crear SQLite source y CSV source.
9. Unir por `vehicle_id`.
10. Mostrar un caso de marca inconsistente.
11. Agregar la regla de homologacion y separar pass/reject.
12. Escribir SQLite y CSV.
13. Abrir el Plan para conectar canvas con SQL.
14. Comparar el resultado con `etl.py`.

## Preguntas durante la demo

- ¿Que representa una fila en cada fuente?
- ¿Cual es la clave de integracion?
- ¿Que pasa si la clave existe, pero marca y modelo no coinciden?
- ¿Por que no conviene eliminar los rechazos?
- ¿Que diferencia hay entre una vista previa y una validacion?
- ¿Que parte deberia quedar registrada para investigar una falla?

## Limites que conviene declarar

- La práctica usa fuentes locales y pequeñas.
- No se evalua rendimiento distribuido.
- No se usan credenciales ni servicios cloud.
- Duckle ayuda a construir y observar el flujo; no decide si la integración es
  semánticamente correcta.
- La implementación Python sigue siendo la referencia para hablar de pruebas,
  configuración, logging e idempotencia.

## Puente a la actividad

Despues de la primera ejecucion y del caso ETL, entregar `actividad_extension.md`. El estudiante debe
agregar la segunda lookup JSON y justificar su tipo de join, sus rechazos y su
estrategia de carga.
