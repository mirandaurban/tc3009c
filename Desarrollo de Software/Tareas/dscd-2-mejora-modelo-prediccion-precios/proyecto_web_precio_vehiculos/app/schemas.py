from typing import Literal

from pydantic import BaseModel, Field

Fuel = Literal["Diesel", "Petrol", "CNG", "LPG"]
SellerType = Literal["Individual", "Dealer", "Trustmark Dealer"]
Transmission = Literal["Manual", "Automatic"]
Owner = Literal[
    "First Owner",
    "Second Owner",
    "Third Owner",
    "Fourth & Above Owner",
    "Test Drive Car",
]


class VehicleFeatures(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    fuel: Fuel
    seats: str = Field(min_length=1, max_length=5)
    seller_type: SellerType
    transmission: Transmission
    owner: Owner
    year: int = Field(ge=1990, le=2026)
    km_driven: float = Field(ge=0, le=800000)
    mileage: float = Field(ge=0, le=50)
    engine: float = Field(ge=500, le=6000)
    max_power: float = Field(ge=0, le=600)
    torque: float = Field(ge=0, le=1000)


class PriceResponse(BaseModel):
    estimated_price: float
    currency: str
    model_version: str


class PricePredictionHistoryResponse(BaseModel):
    id: int
    created_at: str
    name: str
    fuel: str
    seats: str
    seller_type: str
    transmission: str
    owner: str
    year: int
    km_driven: float
    mileage: float
    engine: float
    max_power: float
    torque: float
    estimated_price: float
    model_version: str