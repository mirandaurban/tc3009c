
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
import skops.io as sio
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def prohibido(*args, **kwargs):
    raise RuntimeError("Esta prueba prohíbe volver a entrenar")

# Entrenar o reajustar una representación debe fallar en este proceso.
Pipeline.fit = prohibido
TfidfVectorizer.fit = prohibido
TfidfVectorizer.fit_transform = prohibido
LogisticRegression.fit = prohibido

carpeta = Path(sys.argv[1])
tipos = sio.get_untrusted_types(file=carpeta/"baseline.skops")
if tipos:
    raise RuntimeError("Revisar tipos antes de autorizar carga: "+str(tipos))
recuperado = sio.load(carpeta/"baseline.skops", trusted=[])
referencia = pd.read_csv(carpeta/"predicciones.csv", keep_default_na=False)
observadas = recuperado.predict(referencia.text_processed).tolist()
assert observadas == referencia.prediction.tolist(), "Cambió alguna predicción"
resultado = {"estado":"PASS", "filas":len(referencia), "fit_prohibido":True,
             "tipos_no_confiables":tipos}
(carpeta/"recarga.json").write_text(json.dumps(resultado,indent=2))
print(json.dumps(resultado))
