from typing import Literal

from pydantic import BaseModel, Field

Transmision = Literal["Automatica", "Manual"]


class VehicleFeatures(BaseModel):
    marca: str = Field(min_length=1, max_length=40)
    modelo: str = Field(min_length=1, max_length=40)
    anio: int = Field(ge=2000, le=2026)
    km: int = Field(ge=0, le=400000)
    transmision: Transmision


class PriceResponse(BaseModel):
    estimated_price: float
    currency: str
    model_version: str


class PricePredictionHistoryResponse(BaseModel):
    id: int
    created_at: str
    marca: str
    modelo: str
    anio: int
    km: int
    transmision: str
    estimated_price: float
    model_version: str
