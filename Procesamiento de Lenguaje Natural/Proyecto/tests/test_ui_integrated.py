from pathlib import Path
import secrets
import pytest
from streamlit.testing.v1 import AppTest
from chatpnl_labs import http_client
from chatpnl_labs.http_client import ServiceError
from chatpnl_labs.auth_api import issue_token
from conftest import account
P=Path(__file__).resolve().parents[1]

@pytest.fixture
def linked(integrated,monkeypatch):
    client,_,secret,app=integrated
    def bridge(base,method,path,token=None,**kwargs):
        headers={"Authorization":f"Bearer {token}"} if token else {}
        response=client.request(method,path,headers=headers,**kwargs)
        if response.status_code>=400:
            raise ServiceError(f"HTTP {response.status_code}: solicitud rechazada",response.status_code)
        return None if response.status_code==204 else response.json()
    monkeypatch.setattr(http_client,"request_json",bridge)
    return client,secret

def button(ui,label,sidebar=False):
    return next(b for b in (ui.sidebar.button if sidebar else ui.button) if b.label==label)

def login(ui,name,password):
    ui.radio[0].set_value("Iniciar sesión").run()
    ui.text_input[0].set_value(name);ui.text_input[1].set_value(password)
    button(ui,"Enviar").click().run()
    assert not ui.exception

def test_single_ui_register_chat_switch_rename_relogin_and_delete(linked):
    client,_=linked;password=secrets.token_urlsafe(24)
    ui=AppTest.from_file(str(P/'app.py')).run(timeout=30)
    assert len(ui.chat_input)==0
    ui.radio[0].set_value("Registrar usuario").run()
    ui.text_input[0].set_value("interfaz_a");ui.text_input[1].set_value(password)
    button(ui,"Enviar").click().run();assert ui.success
    login(ui,"interfaz_a",password)
    button(ui,"Nueva conversación",True).click().run();first=ui.session_state["chatpnl_active"]
    ui.chat_input[0].set_value("cuántos libros puedo pedir").run()
    assert len(ui.chat_message)==2 and "tres libros" in ui.chat_message[-1].markdown[0].value
    assert "prestamos.txt" in ui.chat_message[-1].caption[0].value
    ui.chat_input[0].set_value("¿Cuál es el precio de una laptop?").run()
    assert len(ui.chat_message)==4 and len(ui.chat_message[-1].caption)==0
    button(ui,"Nueva conversación",True).click().run();second=ui.session_state["chatpnl_active"]
    assert first!=second and len(ui.chat_message)==0
    ui.sidebar.selectbox[0].select(first).run();assert len(ui.chat_message)==4
    ui.sidebar.selectbox[0].select(second).run();assert len(ui.chat_message)==0
    ui.sidebar.text_input[0].set_value("Segunda prueba");button(ui,"Renombrar",True).click().run()
    assert ui.session_state["chatpnl_active"]==second
    button(ui,"Cerrar sesión",True).click().run();assert len(ui.chat_message)==0 and len(ui.chat_input)==0
    login(ui,"interfaz_a",password)
    ui.sidebar.selectbox[0].select(first).run();assert len(ui.chat_message)==4
    assert "prestamos.txt" in ui.chat_message[1].caption[0].value
    ui.sidebar.checkbox[0].check().run();button(ui,"Eliminar conversación",True).click().run()
    assert ui.session_state["chatpnl_active"]==second
    assert len(ui.chat_message)==0 and not ui.exception

def test_expiry_clears_private_session_before_another_account(linked):
    client,secret=linked;a,body=account(client,"primero");_,body_b=account(client,"segundo")
    ui=AppTest.from_file(str(P/'app.py')).run(timeout=30)
    login(ui,body["username"],body["password"])
    button(ui,"Nueva conversación",True).click().run()
    ui.chat_input[0].set_value("libros préstamo").run();assert len(ui.chat_message)==2
    uid=client.get("/auth/me",headers=a).json()["id"]
    ui.session_state["chatpnl_token"]=issue_token(uid,secret,-1)
    ui.session_state["chatpnl_pending"]={"cid":1,"text":"pendiente","request_id":"pendiente"}
    ui.run()
    assert len(ui.chat_message)==0 and len(ui.chat_input)==0
    assert not ui.session_state.filtered_state.get("chatpnl_pending")
    assert not ui.session_state.filtered_state.get("chatpnl_token")
    login(ui,body_b["username"],body_b["password"])
    assert len(ui.chat_message)==0 and len(ui.sidebar.selectbox)==0
