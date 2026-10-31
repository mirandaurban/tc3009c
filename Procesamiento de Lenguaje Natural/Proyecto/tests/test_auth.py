import secrets,os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from chatpnl_labs.auth_api import create_app,issue_token,User

@pytest.fixture
def client(tmp_path):
    secret=secrets.token_urlsafe(48)
    app=create_app(f"sqlite:///{tmp_path/'test.db'}",secret)
    with TestClient(app) as c: yield c,secret,app

def user(c,name):
    # Credencial efímera de test, no secreto real del usuario.
    body={"username":name,"password":secrets.token_urlsafe(24)}
    assert c.post("/auth/register",json=body).status_code==201
    login=c.post("/auth/login",json=body);assert login.status_code==200
    return {"Authorization":"Bearer "+login.json()["access_token"]},body

def test_register_login_argon2(client):
    c,secret,app=client;headers,body=user(c,"persona_a")
    assert c.get("/auth/me",headers=headers).json()["username"]==body["username"]
    assert c.post("/auth/register",json=body).status_code==409
    with Session(app.state.engine) as db:
        record=db.scalar(select(User).where(User.username==body["username"]))
        assert record.password_hash.startswith("$argon2id$") and body["password"] not in record.password_hash

def test_bad_login(client):
    c,_,_=client;headers,body=user(c,"persona_a")
    body["password"]="incorrecta_12345"
    assert c.post("/auth/login",json=body).status_code==401

def test_no_invalid_expired_jwt(client):
    c,secret,_=client;user(c,"persona_a")
    for token in [None,"invalid",issue_token(1,secret,-1),issue_token(1,secrets.token_urlsafe(48)),issue_token(999,secret)]:
        headers={"Authorization":f"Bearer {token}"} if token else {}
        assert c.get("/auth/me",headers=headers).status_code==401

def test_private_ownership(client):
    c,_,_=client;a,_=user(c,"persona_a");b,_=user(c,"persona_b")
    cid=c.post("/conversations",json={"title":"Privada"},headers=a).json()["id"]
    assert c.post(f"/conversations/{cid}/messages",json={"content":"Mensaje de prueba"},headers=a).status_code==201
    assert c.get("/conversations",headers=b).json()==[]
    assert c.get(f"/conversations/{cid}/messages",headers=b).status_code==404
    assert c.post(f"/conversations/{cid}/messages",json={"content":"No permitido"},headers=b).status_code==404
    assert c.delete(f"/conversations/{cid}",headers=b).status_code==404
    assert len(c.get(f"/conversations/{cid}/messages",headers=a).json())==1
    assert c.delete(f"/conversations/{cid}",headers=a).status_code==204
    assert c.get(f"/conversations/{cid}/messages",headers=a).status_code==404

def test_secret_required(tmp_path,monkeypatch):
    monkeypatch.setenv("CHATPNL_JWT_SECRET","")
    with pytest.raises(RuntimeError):create_app(f"sqlite:///{tmp_path/'x.db'}","")

@pytest.mark.mysql
def test_mysql_real():
    url=os.getenv("CHATPNL_TEST_MYSQL_URL")
    if not url: pytest.skip("Configurar base MySQL de pruebas vacía: docs/MYSQL.md")
    app=create_app(url,secrets.token_urlsafe(48))
    with TestClient(app) as c:
        name="test_"+secrets.token_hex(5)
        headers,_=user(c,name)
        cid=c.post("/conversations",headers=headers,json={"title":"Persistencia MySQL"}).json()["id"]
        assert c.post(f"/conversations/{cid}/messages",headers=headers,json={"content":"Prueba"}).status_code==201
    # Reiniciar aplicación conserva identidad y datos: no sustituir por SQLite.
    with TestClient(create_app(url,secrets.token_urlsafe(48))) as c:
        # El token anterior usa otra clave y debe rechazarse.
        assert c.get("/auth/me",headers=headers).status_code==401
    with Session(app.state.engine) as db:
        assert db.scalar(select(User).where(User.username==name)) is not None
