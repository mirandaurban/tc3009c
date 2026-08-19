"""
Schema del API

Permite filtrar las solicitudes para verificar que los datos ingresados sean válidos
"""

from typing import Literal
from pydantic import BaseModel, Field


class BankFeatures(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Edad del cliente (18-100)")
    job: Literal[
        "admin.", "unknown", "unemployed", "management", "housemaid",
        "entrepreneur", "student", "blue-collar", "self-employed",
        "retired", "technician", "services"
    ]
    marital: Literal["married", "divorced", "single"]
    education: Literal["unknown", "secondary", "primary", "tertiary"]
    balance: int = Field(..., ge=-100_000, le=1_000_000, description="Balance anual promedio (EUR)")
    housing: Literal["yes", "no"]
    loan: Literal["yes", "no"]
    campaign: int = Field(..., ge=1, le=100, description="Número de contactos en esta campaña")