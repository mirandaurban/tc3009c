"""Datos, normalización conservadora y métricas auditables."""
from pathlib import Path
import json, re, unicodedata, random
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LABELS = ['acceso', 'conectividad', 'pagos', 'software']
SEED = 42

def seed_all(seed=SEED,neural=True):
    random.seed(seed); np.random.seed(seed)
    if neural:
        import torch
        torch.manual_seed(seed); torch.set_num_threads(2)

def load_requests():
    df = pd.read_csv(ROOT/'07_datos/solicitudes.csv')
    validate_splits(df)
    return df

def load_json(name):
    return json.loads((ROOT/'07_datos'/name).read_text(encoding='utf-8'))

def validate_splits(df):
    required = {'id','text','label','family','split'}
    if not required <= set(df):
        raise ValueError(f'Faltan columnas: {required-set(df)}')
    if df.id.duplicated().any() or df.text.isna().any():
        raise ValueError('IDs duplicados o textos ausentes')
    if df.groupby('family').split.nunique().max() > 1:
        raise ValueError('Fuga: una familia aparece en más de una partición')
    if df.groupby('text').split.nunique().max() > 1:
        raise ValueError('Fuga: texto idéntico en distintas particiones')
    if set(df.split) != {'train','validation','test'}:
        raise ValueError('Se requieren train, validation y test')
    return True

def normalize(text):
    if not isinstance(text, str):
        raise TypeError('Se esperaba una cadena de texto')
    # Se conservan negación, acentos y signos con valor lingüístico.
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()

def redact(text):
    return re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[CORREO]', text)

def words(text):
    return re.findall(r'\w+|[^\w\s]', normalize(text).lower(), flags=re.UNICODE)

def rule_label(text):
    t=normalize(text).lower()
    rules=[('pagos',r'factura|pag[oó]|cobro|cargo|tarjeta|reembolso'),('acceso',r'contrase|sesión|usuario|c[oó]digo|cuenta|acceso'),('conectividad',r'wifi|red|internet|vpn|conexión')]
    return next((label for label,pattern in rules if re.search(pattern,t)), 'software')

def exact_span_scores(gold, predicted):
    """Micro por tuplas (documento, inicio, fin, tipo), coincidencia exacta."""
    g=set(gold); p=set(predicted); tp=len(g&p)
    precision=tp/len(p) if p else 0.0
    recall=tp/len(g) if g else 0.0
    return dict(tp=tp,fp=len(p-g),fn=len(g-p),precision=precision,recall=recall,
                f1=2*precision*recall/(precision+recall) if precision+recall else 0.0)

def rule_entities(text):
    spans=[]
    for label,pat in [('FOLIO',r'\bINC-\d{4}\b'),('PRODUCTO',r'\b(?:AulaPro|MesaApp|NubeTec)\b')]:
        spans.extend((m.start(),m.end(),label) for m in re.finditer(pat,text))
    return sorted(spans)
