"""Encoder abierto en CPU, siempre desde una carpeta local; nunca sustituye con vectores falsos."""
from pathlib import Path
from dataclasses import asdict
import numpy as np
MODEL_ID="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISION="e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
def load_encoder(path):
    if not path or not Path(path).is_dir():
        raise FileNotFoundError("Modelo contextual pendiente: configure CHATPNL_MODEL_PATH")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(str(path),device="cpu",local_files_only=True)
def semantic_search(encoder, chunks, query, k=3):
    # Matrices de documentos se crean por llamada/sesión; no hay índice privado global.
    matrix=encoder.encode([c.text for c in chunks],normalize_embeddings=True)
    vector=encoder.encode([query],normalize_embeddings=True)[0]
    scores=matrix @ vector
    return [{**asdict(chunks[i]),"score":float(scores[i])} for i in np.argsort(-scores,kind="stable")[:k]]
