import sys
from pathlib import Path
# Instalación editable recomendada; compatibilidad para la ejecución directa del árbol del curso.
project=Path(__file__).resolve().parents[1]
for parent in project.parents:
    if (parent/"src/chatpnl_labs").is_dir(): sys.path.insert(0,str(parent/"src"));break


import secrets
import pytest
from fastapi.testclient import TestClient
from chatpnl_labs.starter_api import create_app

@pytest.fixture
def integrated(tmp_path):
    url=f"sqlite:///{tmp_path/'chat.db'}"
    secret=secrets.token_urlsafe(48)
    app=create_app(url,secret)
    with TestClient(app) as client:
        yield client,url,secret,app

def account(client,name):
    payload={"username":name,"password":secrets.token_urlsafe(24)}
    assert client.post("/auth/register",json=payload).status_code==201
    result=client.post("/auth/login",json=payload)
    assert result.status_code==200
    return {"Authorization":"Bearer "+result.json()["access_token"]},payload
