from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, list_recent_predictions, save_prediction
from app.model_service import predict
from app.schemas import PricePredictionHistoryResponse, PriceResponse, VehicleFeatures

app = FastAPI(title="Vehicle Price Estimator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict-price", response_model=PriceResponse)
def predict_price(features: VehicleFeatures) -> PriceResponse:
    try:
        payload = features.model_dump()
        result = predict(payload)
        save_prediction(payload, result)
        return PriceResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


@app.get("/api/price-predictions", response_model=list[PricePredictionHistoryResponse])
def get_recent_predictions(limit: int = 20) -> list[PricePredictionHistoryResponse]:
    try:
        rows = list_recent_predictions(limit=limit)
        return [PricePredictionHistoryResponse(**row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
