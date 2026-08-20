# Proyecto Base Web - Precio de Vehiculos (Regresion Lineal)

Continuacion de la Clase 2, ahora con un problema de **regresion**: estimar
el precio de un vehiculo usado. La idea de uso es un valuador para un asesor
de ventas: captura los datos del vehiculo, la web llama al backend, el
backend consulta la inferencia del modelo y devuelve el precio estimado.
Cada consulta queda guardada en SQLite para seguimiento.

## Requisito de version de Python

Usar Python 3.11 o 3.12 para la clase.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## 1) Entrenar el modelo

```bash
python3 scripts/train_model.py
```

Esto genera:

- `models/vehicle_price_v1.joblib` — pipeline (preprocessing + Regresion Lineal)
- `models/metrics.json` — MAE, RMSE y R2 del baseline

## 2) Correr backend

```bash
bash scripts/run_backend.sh
```

Abrir en navegador:

- http://127.0.0.1:9011
- API docs: http://127.0.0.1:9011/docs

Ejemplo de consumo desde otra app (slide 8 de la clase):

```bash
curl -X POST http://127.0.0.1:9011/predict-price \
  -H "Content-Type: application/json" \
  -d '{
    "marca": "Nissan",
    "modelo": "Sentra",
    "anio": 2022,
    "km": 38500,
    "transmision": "Automatica"
  }'
```

Respuesta esperada:

```json
{
  "estimated_price": 318500.0,
  "currency": "MXN",
  "model_version": "v1"
}
```

## 3) Correr frontend por separado (opcional)

```bash
bash scripts/run_frontend.sh
```

Abrir en navegador:

- http://127.0.0.1:9010

El frontend usa `app/static/config.js` para apuntar al backend y consume:

- `POST /predict-price` para inferencia
- `GET /api/price-predictions` para historial reciente

## 4) Levantar ambos con un solo script

```bash
bash scripts/run_site.sh
```

Esto deja:

- frontend en `http://127.0.0.1:9010`
- backend en `http://127.0.0.1:9011`

## Endpoints

- `GET /api/health`
- `POST /predict-price`
- `GET /api/price-predictions`

### Flujo de consumo

1. El usuario llena el formulario web con los datos del vehiculo.
2. El frontend envia un `fetch` con JSON a `POST /predict-price`.
3. FastAPI valida el payload (Pydantic) y llama al pipeline serializado.
4. El pipeline aplica el mismo preprocesamiento del entrenamiento y predice.
5. La API devuelve `estimated_price`, `currency` y `model_version`.
6. La prediccion se guarda en SQLite.
7. El frontend consulta `GET /api/price-predictions` para mostrar historial.

## Arquitectura minima (slide 9)

```
Fuentes (dataset historico)
        ↓
Data / Training (validar → preparar → entrenar → evaluar → modelo versionado)
        ↓
vehicle_price_v1.joblib
        ↓
Inference Service (FastAPI, /predict-price)
        ↓
Consumidores (frontend web, otra app, otro sistema)
```

## Buenas practicas aplicadas

- **Validacion**: `app/schemas.py` usa Pydantic (`VehicleFeatures`) para
  aceptar solo datos con el tipo y rango esperado antes de llegar al modelo.
- **Versionado del modelo**: cada respuesta incluye `model_version`
  (`vehicle_price_v1`), y el pipeline vive en un archivo `.joblib` separado
  del codigo.
- **Separacion train/inference**: `scripts/train_model.py` entrena offline;
  la API (`app/model_service.py`) solo carga el pipeline ya entrenado y
  predice. Entrenar y predecir son procesos distintos.
- **Testing**: `tests/test_health.py` valida que el servicio este disponible.
- **Monitoring**: `GET /api/health` sirve como chequeo basico de
  disponibilidad para un monitor externo.
- **Seguridad** (pendientes a discutir en clase, no implementados aqui por
  alcance): autenticacion de quien consume la API, secrets fuera del codigo,
  HTTPS en transito.
