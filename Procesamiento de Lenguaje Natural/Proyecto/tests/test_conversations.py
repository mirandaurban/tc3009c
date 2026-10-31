from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event,select,func
from sqlalchemy.orm import Session
from chatpnl_labs.auth_api import User,Conversation,Message,ChatTurn,issue_token
from chatpnl_labs.starter_api import create_app
from chatpnl_labs import core
from conftest import account

def conversation(client,headers,title="Primera"):
    result=client.post("/conversations",headers=headers,json={"title":title})
    assert result.status_code==201
    return result.json()["id"]

def turn(client,headers,cid,text="cuántos libros puedo pedir",request_id=None):
    return client.post(f"/conversations/{cid}/query",headers=headers,json={"text":text,"request_id":request_id or str(uuid4())})

def test_history_survives_new_api_with_sources_and_abstention(integrated):
    c,url,secret,_=integrated;headers,payload=account(c,"historial")
    cid=conversation(c,headers)
    positive=turn(c,headers,cid);assert positive.status_code==200
    assert positive.json()["abstained"] is False
    assert positive.json()["references"][0]["source"]=="prestamos.txt"
    negative=turn(c,headers,cid,"¿Cuál es el precio de una laptop?")
    assert negative.status_code==200 and negative.json()["abstained"] is True
    before=c.get(f"/conversations/{cid}/messages",headers=headers).json()
    assert [m["role"] for m in before]==["user","assistant","user","assistant"]
    assert before[1]["references"]==positive.json()["references"]
    assert before[-1]["references"]==[] and before[-1]["abstained"] is True
    with TestClient(create_app(url,secret)) as restarted:
        login=restarted.post("/auth/login",json=payload)
        again={"Authorization":"Bearer "+login.json()["access_token"]}
        assert restarted.get(f"/conversations/{cid}/messages",headers=again).json()==before

def test_user_cannot_read_change_delete_or_query_foreign_history(integrated,monkeypatch):
    c,_,_,_=integrated;a,_=account(c,"cuenta_a");b,_=account(c,"cuenta_b")
    cid=conversation(c,a);assert turn(c,a,cid).status_code==200
    def forbidden(*args,**kwargs):raise AssertionError("No recuperar evidencia sin autorizar")
    monkeypatch.setattr(core,"answer",forbidden)
    assert c.get("/conversations",headers=b).json()==[]
    assert c.get(f"/conversations/{cid}/messages",headers=b).status_code==404
    assert c.patch(f"/conversations/{cid}",headers=b,json={"title":"Ajena"}).status_code==404
    assert c.delete(f"/conversations/{cid}",headers=b).status_code==404
    assert turn(c,b,cid).status_code==404
    assert len(c.get(f"/conversations/{cid}/messages",headers=a).json())==2

def test_retry_returns_saved_answer_without_duplicate_or_recomputation(integrated,monkeypatch):
    c,_,_,app=integrated;h,_=account(c,"reintento");cid=conversation(c,h);rid=str(uuid4())
    first=turn(c,h,cid,request_id=rid);assert first.status_code==200
    def forbidden(*args,**kwargs):raise AssertionError("Un reintento no vuelve a responder")
    monkeypatch.setattr(core,"answer",forbidden)
    repeated=turn(c,h,cid,request_id=rid)
    assert repeated.status_code==200 and repeated.json()["replayed"] is True
    assert repeated.json()["assistant_message_id"]==first.json()["assistant_message_id"]
    assert repeated.json()["references"]==first.json()["references"]
    assert turn(c,h,cid,"Otro texto",rid).status_code==409
    assert len(c.get(f"/conversations/{cid}/messages",headers=h).json())==2
    with Session(app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn))==1

def test_failed_turn_rolls_back_question_answer_and_sources(integrated):
    c,_,_,app=integrated;h,_=account(c,"atomico");cid=conversation(c,h)
    def fail(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().startswith("INSERT INTO chatpnl_turns"):
            raise RuntimeError("Fallo de prueba antes de confirmar")
    event.listen(app.state.engine,"before_cursor_execute",fail)
    try:
        with pytest.raises(RuntimeError,match="Fallo de prueba"):
            turn(c,h,cid)
    finally:
        event.remove(app.state.engine,"before_cursor_execute",fail)
    assert c.get(f"/conversations/{cid}/messages",headers=h).json()==[]
    assert turn(c,h,cid).status_code==200

def test_rename_delete_removes_turns_and_messages(integrated):
    c,_,_,app=integrated;h,_=account(c,"borrado");cid=conversation(c,h)
    assert turn(c,h,cid).status_code==200
    assert c.patch(f"/conversations/{cid}",headers=h,json={"title":"Renombrada"}).json()["title"]=="Renombrada"
    assert c.delete(f"/conversations/{cid}",headers=h).status_code==204
    assert c.get("/conversations",headers=h).json()==[]
    assert c.get(f"/conversations/{cid}/messages",headers=h).status_code==404
    with Session(app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(ChatTurn))==0
        assert db.scalar(select(func.count()).select_from(Message))==0

@pytest.mark.parametrize("text",["","   ","a"*2001])
def test_invalid_query_does_not_write_messages(integrated,text):
    c,_,_,_=integrated;h,_=account(c,"validacion");cid=conversation(c,h)
    assert turn(c,h,cid,text).status_code==422
    assert c.get(f"/conversations/{cid}/messages",headers=h).json()==[]

def test_expired_token_cannot_read_or_send(integrated):
    c,_,secret,_=integrated;h,_=account(c,"expiracion");cid=conversation(c,h)
    uid=c.get("/auth/me",headers=h).json()["id"]
    expired={"Authorization":"Bearer "+issue_token(uid,secret,-1)}
    assert c.get(f"/conversations/{cid}/messages",headers=expired).status_code==401
    assert turn(c,expired,cid).status_code==401
    assert c.get(f"/conversations/{cid}/messages",headers=h).json()==[]


@pytest.mark.mysql
def test_integrated_mysql_restart_and_delete():
    import os,secrets
    url=os.getenv("CHATPNL_TEST_MYSQL_URL")
    if not url:pytest.skip("Preparar una base MySQL de pruebas")
    secret=secrets.token_urlsafe(48)
    with TestClient(create_app(url,secret)) as c:
        headers,payload=account(c,"chat_"+secrets.token_hex(5))
        cid=conversation(c,headers)
        result=turn(c,headers,cid)
        assert result.status_code==200
        saved=c.get(f"/conversations/{cid}/messages",headers=headers).json()
        assert saved[-1]["references"]==result.json()["references"]
    with TestClient(create_app(url,secret)) as c:
        login=c.post("/auth/login",json=payload)
        headers={"Authorization":"Bearer "+login.json()["access_token"]}
        assert c.get(f"/conversations/{cid}/messages",headers=headers).json()==saved
        assert c.delete(f"/conversations/{cid}",headers=headers).status_code==204
        assert c.get(f"/conversations/{cid}/messages",headers=headers).status_code==404


def test_configuration_reads_env_from_current_project_folder(tmp_path,monkeypatch):
    import secrets
    monkeypatch.chdir(tmp_path)
    for name in ["CHATPNL_DATABASE_URL","CHATPNL_JWT_SECRET"]:
        # Registrar también su ausencia para restaurarla tras cargar el .env de prueba.
        monkeypatch.setenv(name,"")
        monkeypatch.delenv(name)
    (tmp_path/".env").write_text(f"CHATPNL_DATABASE_URL=sqlite:///{tmp_path/'configured.db'}\nCHATPNL_JWT_SECRET={secrets.token_urlsafe(48)}\n")
    with TestClient(create_app()) as c:
        headers,_=account(c,"configurada")
        assert c.get("/auth/me",headers=headers).json()["username"]=="configurada"
    assert (tmp_path/'configured.db').exists()


@pytest.mark.mysql
def test_integrated_mysql_concurrent_retries():
    import os,secrets
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    url=os.getenv("CHATPNL_TEST_MYSQL_URL")
    if not url:pytest.skip("Preparar una base MySQL de pruebas")
    app=create_app(url,secrets.token_urlsafe(48))
    with TestClient(app) as c:
        headers,_=account(c,"doble_"+secrets.token_hex(5));cid=conversation(c,headers);rid=str(uuid4())
        together=Barrier(2)
        def align_auth(conn,cursor,statement,parameters,context,executemany):
            # Ambas lecturas de autenticación comienzan antes de guardar el turno.
            if "FROM chatpnl_users" in statement:
                together.wait(timeout=10)
        event.listen(app.state.engine,"after_cursor_execute",align_auth)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _:turn(c,headers,cid,request_id=rid),range(2)))
        finally:
            event.remove(app.state.engine,"after_cursor_execute",align_auth)
        assert all(result.status_code==200 for result in results)
        assert {result.json()["replayed"] for result in results}=={True,False}
        assert len(c.get(f"/conversations/{cid}/messages",headers=headers).json())==2
