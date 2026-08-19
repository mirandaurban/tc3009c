"""
API de inferencia

Recibe solicitudes y regresa una respuesta (predicción) con base al modelo

Comando para ejecutar en dev:
    fastapi dev main.py
"""
import joblib
import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Definir el input que aceptará el API
from schemas import BankFeatures

# Cargar el modelo ya entrenado
clf = joblib.load("../models/bank_marketing_pipeline.joblib")

# Crear FastAPI
app = FastAPI(
    title="Bank Marketing Predictor API",
    description=(
        "API de inferencia para estimar la propensión de un cliente a contratar un depósito a plazo, usando un pipeline de Regresión Logística"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default endpoint
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Bank Marketing Predictor API.",
    }

# Definir endpoint de predicción
@app.post("/predict")
def predict(data: BankFeatures):
    """
    Recibe los datos de un cliente, ejecuta el pipeline de inferencia y
    devuelve predicción + probabilidad.
    """
    try:
        test_data = pd.DataFrame([{
            "age": data.age,
            "job": data.job,
            "marital": data.marital,
            "education": data.education,
            "balance": data.balance,
            "housing": data.housing,
            "loan": data.loan,
            "campaign": data.campaign
        }])

        # Obtener la predicción y las probabilidades de las clases
        prediction = clf.predict(test_data)[0]
        probabilities = clf.predict_proba(test_data)[0]

        # Obtener la probabilidad de la clase "yes"
        yes_index = list(clf.classes_).index("yes")
        probability = probabilities[yes_index]

        # Clasificar el resultado para mejor entendimiento del usuario
        classification = (
            "Potencialmente interesado"
            if prediction == "yes"
            else "Potencialmente no interesado"
        )

        return {
            "prediction": prediction,
            "probability": round(float(probability), 2),
            "classification": classification
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error al procesar la predicción: {str(e)}")

"""
Caso de prueba utilizado:

{
  "age": 41,
  "job": "technician",
  "marital": "married",
  "education": "secondary",
  "balance": 3200,
  "housing": "yes",
  "loan": "no",
  "campaign": 2
}


Resultado obtenido:

{
  "prediction": "no",
  "probability": 0.4,
  "classification": "Potencialmente no interesado"
}

Para obtener este resultado se usó predict(X) con el fin de definir la matriz de 
datos para la que queremos obtener las predicciones, en este caso la del ejemplo.
Por otro lado, la probabilidad surge de la función de predict_proba(X) que permite
obtener las estimaciones devueltas por el modelo para todas las clases, ordenadas 
por etiquetas de clases; de esos resultados, se obtuvo la estimaciones para la 
etiqueta de "yes". Es importante notar que predict() simplemente escoge la clase 
con mayor probabilidad, por lo que es 40% es la probabilidad estimada por la 
regresión para la clase "yes".
"""

# Referencias:
# First steps - FastAPI. (n.d.). https://fastapi.tiangolo.com/tutorial/first-steps/#step-4-define-the-path-operation-function 
# GeeksforGeeks. (2026, May 11). Deploying ML Models as API using FastAPI. https://www.geeksforgeeks.org/machine-learning/deploying-ml-models-as-api-using-fastapi/ 
# LogisticRegression. (n.d.). Scikit-learn. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html?utm_source=chatgpt.com

# Herramienta: Chat GPT
# • Uso realizado: Se utilizó para corrección de errores y para obtener un mejor formato del código.
# • Secciones donde se utilizó: Este archivo para los detalles del API (sección de Crear FASTAPI) 
#   y para corregir errores que surgieron en el proceso de construcción (específicamente con issues de CORS).
# • Validación realizada por el estudiante: Véase las fuentes usadas en esta sección.
# Confirmo que revisé, verifiqué y asumo la responsabilidad del contenido final entregado