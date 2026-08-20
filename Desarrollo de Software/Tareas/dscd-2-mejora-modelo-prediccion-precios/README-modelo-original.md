# Clase 3 — De los datos a un servicio de inferencia (README original del código dado por el profesor)

Caso practico: estimar el precio de un vehiculo usado (regresion), con un
contraste breve de clasificacion (Regresion Logistica vs KNN).

Enfoque de la clase: **como llevar un modelo a una solucion de software**, no
solo como entrenarlo.

## Contenido

- `Clase03_Autos_Precio.ipynb` — recorrido completo: EDA rapido, estadistica
  util, preparacion de datos, Regresion Lineal (baseline), metricas (MAE,
  RMSE, R2), y un contraste corto de clasificacion (Regresion Logistica y
  KNN). Al final entrena y guarda el pipeline que usa la API.
- `proyecto_web_precio_vehiculos/` — servicio de inferencia (FastAPI) que
  carga ese pipeline y lo expone como `POST /predict-price`, mas un frontend
  simple para consumirlo. Es la continuacion natural de la Clase 2, ahora con
  un problema de regresion en vez de clasificacion.

## Mapa slides → artefactos

| Slide | Tema                                   | Donde esta en el repo                     |
| ----- | -------------------------------------- | ----------------------------------------- |
| 1     | Regresion vs clasificacion             | Notebook, seccion 1                       |
| 2     | Revision rapida del dataset            | Notebook, seccion 2                       |
| 3     | Estadistica util antes de modelar      | Notebook, seccion 3                       |
| 4     | Preparar X/y, train/test, Pipeline     | Notebook, seccion 4                       |
| 5     | Regresion Lineal como baseline         | Notebook, seccion 5                       |
| 6     | MAE / RMSE / R2                        | Notebook, seccion 6                       |
| 7     | Regresion Logistica vs KNN             | Notebook, seccion 7                       |
| 8     | Del modelo al servicio de inferencia   | `proyecto_web_precio_vehiculos/` completo |
| 9     | Arquitectura minima + buenas practicas | `proyecto_web_precio_vehiculos/README.md` |

## Como correrlo

```bash
cd proyecto_web_precio_vehiculos
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/train_model.py
bash scripts/run_site.sh
```

Frontend: http://127.0.0.1:9010
Backend: http://127.0.0.1:9011 (docs en `/docs`)
