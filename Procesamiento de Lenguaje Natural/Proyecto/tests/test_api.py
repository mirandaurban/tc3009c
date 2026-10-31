import pytest
from fastapi.testclient import TestClient
from chatpnl_labs.simple_api import app
from chatpnl_labs.starter_api import create_app

def test_health_echo_analyze():
    with TestClient(app) as c:
        assert c.get("/health").json()["status"]=="ok"
        assert c.post("/api/v1/echo",json={"text":"hola mundo"}).json()=={"text":"hola mundo"}
        assert c.post("/api/v1/analyze",json={"text":"hola mundo"}).json()=={"words":2,"characters":10}
@pytest.mark.parametrize("body",[{}, {"text":""},{"text":"   "},{"text":"a"*2001},{"text":12}])
def test_422(body): assert TestClient(app).post("/api/v1/echo",json=body).status_code==422
def test_starter_rejects_anonymous_chat(integrated):
    from uuid import uuid4
    c,_,_,_=integrated
    assert c.get("/health").json()=={"status":"ok"}
    assert c.post("/conversations/1/query",json={"text":"libros préstamo","request_id":str(uuid4())}).status_code==401
    assert c.post("/api/v1/query",json={"text":"libros préstamo"}).status_code==404
