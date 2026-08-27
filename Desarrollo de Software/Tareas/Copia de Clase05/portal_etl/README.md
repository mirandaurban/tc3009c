# Portal ETL — Clase 5

Sitio local muy simple para ejecutar los 3 ejemplos de la clase y ver, en
vivo, que etapa del pipeline (`EXTRACT`, `TRANSFORM`, `LOAD`, etc.) esta
corriendo en cada uno. No reemplaza los ejemplos: solo llama al
`run_etl.sh` de cada carpeta como subproceso y transmite su salida real al
navegador.

## Levantar el sitio

Desde esta carpeta:

```bash
./setup.sh   # crea el entorno virtual e instala Flask + deps de los 3 ejemplos
./start.sh   # levanta el portal en http://127.0.0.1:5050
```

Abre [http://127.0.0.1:5050](http://127.0.0.1:5050) en el navegador.

Cada tarjeta muestra:

- El motor/patron usado (`ETL` en pandas+SQLite para los ejemplos 1 y 2,
  `ELT` en DuckDB+SQL para el ejemplo 3).
- El diagrama de etapas de ESE ejemplo en particular (el ejemplo 1 solo
  tiene 3 etapas; el ejemplo 2 tiene las 9 completas de la clase).
- Un boton "Ejecutar" que corre el pipeline real y muestra su log.

Conforme el log real va imprimiendo lineas como `EXTRACT:`, `VALIDATE:`,
`QUALITY GATE:`, etc., la etapa correspondiente del diagrama se ilumina en
amarillo (en curso) y despues en verde (completada). Si el proceso termina
con error, el boton queda en rojo.

## Como funciona (arquitectura del portal)

```text
navegador
   |  GET /api/examples          (metadata: stages, tech, descripcion)
   |  GET /run/<id>  (SSE)        (una linea de log = un evento)
   v
app.py (Flask)
   |  subprocess.Popen(["bash", "run_etl.sh"], cwd=<carpeta del ejemplo>)
   v
ejemplo_1 / ejemplo_2 / ejemplo_3   (los mismos scripts que se correrian a mano)
```

`app.py` no interpreta ni transforma nada: solo agrega metadatos de
presentacion (titulo, etapas esperadas, badge ETL/ELT) y reenvia stdout
linea por linea.

## Detener el portal

`Ctrl+C` en la terminal donde corre `./start.sh`.

## Troubleshooting

Si `./setup.sh` falla por un error SSL/certificados al descargar paquetes
(común en redes corporativas o entornos con proxy), corre `pip install`
manualmente con tu configuración de red habitual, o usa el intérprete de
Python que ya tengas configurado en tu editor en vez de crear un venv
nuevo.
