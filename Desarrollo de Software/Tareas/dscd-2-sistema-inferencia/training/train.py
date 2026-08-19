"""
Entrenamiento del modelo de Regresión Logística con el objetivo de que sea consumido por un backend web.

Al final del código puede verse el análisis de los resultados y referencias utilizadas.
"""

# Librerías necesarias para el análisis
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression # Modelo que se eligió utilizar para este análisis
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder 
# OneHotEncoder transforma datos categóricos en un formato binario en columnas binarias para cada categoría única de una característica

# # # # # # # # # # # # # # 
# Declaración de variables #
# # # # # # # # # # # # # # 

# Dirección del dataset
DIRECTORY = Path(__file__).resolve().parent.parent
DATA_PATH = DIRECTORY / "data" / "bank.csv"
MODEL_PATH = DIRECTORY / "models" / "bank_marketing_pipeline.joblib"

# Variables predictorias y objetivo que usará el sistema
numeric_features = ["age", "balance", "campaign"] # Para usar con Starndard Scaler (acepta num)
categorical_features = ["job", "marital", "education"] # Para usar con OneHotEncoder para pasar de categótica a binario
binary_features = ["housing", "loan"] # Para usar con OneHotEncoder y clasificar entre "yes" o "no"

target = 'y' # Variable que determina si el cliente contrató o no el depósito

# # # # # # # # # # # # 
# Funciones del código #
# # # # # # # # # # # # 

def load_data(path: Path) -> pd.DataFrame:
    """
    Función para cargar el archivo
    """
    df = pd.read_csv(path, sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df

def build_pipeline() -> Pipeline:
    """
    Función de entrenamiento con Pipeline
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('bin', OneHotEncoder(drop='if_binary'), binary_features),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')), 
        ]
    )
    # Se utiliza el class_weight='balanced' debido a que el dataset tienen una gran diferencia de tamaño entre los grupos de la variable "y"
    # Destaca mayormente el resultado "no" y poco el "yes", además de que el accuracy sin esta variable es alto, mientras que el resto de los valores son igual a 0. 

    return pipeline

def train_model():
    df = load_data(DATA_PATH) # Cargar datos primero

    X = df[numeric_features + binary_features + categorical_features]
    y = df[target]

    # Dividir el conjunto de datos en conjuntos de entrenamiento y pruebas
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline() # Construir el pipeline

    pipeline.fit(X_train, y_train) # Entrenar al modelo con base en el pipeline

    pred = pipeline.predict(X_test)

    # Calcular accuracy, precision, recall y f1-score
    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, pos_label="yes", zero_division=0)
    rec = recall_score(y_test, pred, pos_label="yes")
    f1 = f1_score(y_test, pred, pos_label="yes", zero_division=0)

    print("\n------ MÉTRICAS DE EVALUACIÓN ------")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-score:  {f1:.4f} \n")

    print(classification_report(y_test, pred, zero_division=0))

    """
    Interpretación de resultados:

    ---------- MÉTRICAS DE EVALUACIÓN ORIGINALES ----------
    Accuracy:  0.8851
    Precision: 0.0000
    Recall:    0.0000
    F1-score:  0.0000 

                precision    recall  f1-score   support

            no       0.89      1.00      0.94       801
            yes       0.00      0.00      0.00       104

    accuracy                           0.89       905
    macro avg       0.44      0.50      0.47       905
    weighted avg       0.78      0.89      0.83       905

    ---------- MÉTRICAS DE EVALUACIÓN AJUSTADAS ----------
    Accuracy:  0.6110
    Precision: 0.1612
    Recall:    0.5673
    F1-score:  0.2511 

                precision    recall  f1-score   support

            no       0.92      0.62      0.74       801
            yes       0.16      0.57      0.25       104

    accuracy                           0.61       905
    macro avg       0.54      0.59      0.49       905
    weighted avg       0.83      0.61      0.68       905
    ------------------------------------------------------

    Originalmente, se realizó un análisis sin contemplar que los datos estaban desbalanceados 
    (la cantidad de "no" es bastante mayor a la cantidad de "yes) en la variable de decisión 
    de cliente, por lo que las métricas de evaluación arrojaban 0 y únicamente el accuracy 
    presentaba un valor, de 88% aproximadamente. Al revisar el reporte de clasificación, es 
    claro que hay un error, pues el modelo presenta un precisión alta, de 89%, al predecir 
    "no", pero de 0% al predecir "yes"; lo que revela un modelo de poca utilidad.
    Con el fin de resolver este problema, se utilizó el parámetro de "class_weight='balanced'"
    durante el pipeline de Regresión Logística, ya que este permite equilibrar a la clase 
    minoritaria penalizando a la clase mayoritaria durante el entrenamiento sin la necesidad 
    de añadir más casos de "yes" para balancear el dataset. Con ello se logró modificar las 
    métricas obtenidas, cambiando el accuracy a un 61%, así como la precisión a un 92% para los
    casos de "no" y 16% para los que si. Lo que permite definir con más confizanza (a comparación
    del modelo anterior) si los clientes pertenecen a los clientes potencialmente no interesados 
    en contratar el depóstio. El recall indica qué tan bien puede el modelo detectar a la clase de 
    "interesado" y "no interesado", cuyos valores indican cuántas oportunidades reales se están 
    dejando pasar. Mientras que el F1-score resume el balance entre ambas.
    """

    # Información para el backend
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    metrics = {
    'accuracy': round(float(acc), 4),
    'precision': round(float(prec), 4),
    'recall': round(float(rec), 4),
    'f1-score': round(float(f1), 4),
    'features': numeric_features + binary_features + categorical_features,
    'model_type': 'LogisticRegression'
    }

    # Almacenamiento de las métricas del entrenamiento del modelo
    metrics_path = MODEL_PATH.parent / 'metrics.json'
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModelo y metricas guardados en {MODEL_PATH}")


def main():
    train_model()

if __name__ == "__main__":
    main()

# Referencias:
# Clasificación con datos desbalanceados. (2020, March 3). Aprende Machine Learning. https://www.aprendemachinelearning.com/clasificacion-con-datos-desbalanceados/ 
# GeeksforGeeks. (2025, July 23). How Does the class_weight Parameter in ScikitLearn Work? GeeksforGeeks. https://www.geeksforgeeks.org/machine-learning/how-does-the-classweight-parameter-in-scikit-learn-work/ 
# ¿Qué es la codificación en caliente y cómo implementarla en Python? (2024, July 29). DataCamp. https://www.datacamp.com/es/tutorial/one-hot-encoding-python-tutorial