from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
P=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("folder",sorted((P/"labs").iterdir()),ids=lambda p:p.name)
def test_each_lab_renders(folder,monkeypatch):
    monkeypatch.delenv("CHATPNL_MODEL_PATH",raising=False)
    app=AppTest.from_file(str(folder/"app.py")).run(timeout=30)
    assert not app.exception

def test_chat_roundtrip():
    app=AppTest.from_file(str(P/"labs/02_chat_basico/app.py")).run()
    app.chat_input[0].set_value("hola").run()
    assert len(app.chat_message)==2
    assert "Hola" in app.chat_message[1].markdown[0].value
    app.sidebar.button[0].click().run()
    assert len(app.chat_message)==0

def test_history_switch_and_delete():
    app=AppTest.from_file(str(P/"labs/03_historial_conversaciones/app.py")).run()
    app.chat_input[0].set_value("hola").run()
    assert len(app.chat_message)==2
    app.sidebar.button[0].click().run()
    assert len(app.session_state["conversations"])==2
    assert len(app.chat_message)==0
    ids=list(app.session_state["conversations"])
    app.sidebar.selectbox[0].select(ids[0]).run()
    assert len(app.chat_message)==2
    # Alternar de nuevo detecta reinicios del selector al cambiar su índice inicial.
    app.sidebar.selectbox[0].select(ids[1]).run()
    assert app.session_state["active"]==ids[1]
    assert len(app.chat_message)==0
    app.sidebar.text_input[0].set_value("Segunda conversación")
    app.sidebar.button[1].click().run()
    assert app.session_state["active"]==ids[1]
    app.sidebar.selectbox[0].select(ids[0]).run()
    assert len(app.chat_message)==2
    app.sidebar.selectbox[0].select(ids[1]).run()
    assert len(app.chat_message)==0
    app.sidebar.button[-1].click().run()
    assert len(app.session_state["conversations"])==1

def test_profile_validation_and_persistence():
    app=AppTest.from_file(str(P/"labs/01_streamlit_basico/app.py")).run()
    app.button[0].click().run()
    assert app.error
    app.text_input[0].set_value("alias_ficticio")
    app.button[0].click().run()
    assert app.session_state["profile_data"]["alias"]=="alias_ficticio"
    app.button[1].click().run()
    assert app.session_state["clicks"]==1
    assert app.session_state["profile_data"]["alias"]=="alias_ficticio"

def test_demo_login_validation_and_logout():
    app=AppTest.from_file(str(P/"labs/04_login_ui/app.py")).run()
    app.button[0].click().run()
    assert len(app.error)==2  # aviso permanente + error del formulario
    app.text_input[0].set_value("alias_demo")
    app.checkbox[0].check()
    app.button[0].click().run()
    assert app.success
    app.button[0].click().run()
    assert not app.session_state.filtered_state.get("demo_user")
