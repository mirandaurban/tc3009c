import os
import uuid
from dotenv import load_dotenv
import streamlit as st
from chatpnl_labs.http_client import request_json,ServiceError

load_dotenv()
st.set_page_config(page_title="ChatPNL",layout="wide")
base=os.getenv("CHATPNL_API_URL","http://127.0.0.1:8000")
DATA_KEYS=("chatpnl_token","chatpnl_user","chatpnl_active","chatpnl_pending")

def end_session():
    for key in DATA_KEYS:
        st.session_state.pop(key,None)

def api(method,path,**kwargs):
    return request_json(base,method,path,st.session_state.get("chatpnl_token"),**kwargs)

def show_failure(exc):
    if exc.status_code==401:
        end_session()
        st.session_state.chatpnl_notice="La sesión no es válida o venció. Inicia sesión para recuperar tu historial."
        st.rerun()
    st.error(str(exc))

def select_history():
    st.session_state.chatpnl_active=st.session_state.chatpnl_choice
    st.session_state.pop("chatpnl_pending",None)

def send_turn(pending):
    try:
        api("POST",f"/conversations/{pending['cid']}/query",
            json={"text":pending["text"],"request_id":pending["request_id"]})
        st.session_state.pop("chatpnl_pending",None)
        st.rerun()
    except ServiceError as exc:
        if exc.status_code==401:
            show_failure(exc)
        st.session_state.chatpnl_notice=str(exc)
        st.rerun()

st.title("ChatPNL")
st.caption("Acceso, chat e historial en MySQL. Corpus de consulta: cuatro documentos públicos ficticios de Aurora.")
if notice:=st.session_state.pop("chatpnl_notice",None):
    st.info(notice)
if not st.session_state.get("chatpnl_token"):
    mode=st.radio("Operación",["Iniciar sesión","Registrar usuario"])
    with st.form("chatpnl_credentials",clear_on_submit=True):
        username=st.text_input("Usuario: minúsculas, números o _")
        password=st.text_input("Contraseña de práctica: mínimo 10 caracteres",type="password")
        submitted=st.form_submit_button("Enviar")
    if submitted:
        try:
            result=api("POST","/auth/login" if mode=="Iniciar sesión" else "/auth/register",
                       json={"username":username,"password":password})
            if "access_token" in result:
                end_session()
                st.session_state.chatpnl_token=result["access_token"]
                st.rerun()
            else:
                st.success("Usuario creado. Selecciona Iniciar sesión y vuelve a escribir tus credenciales.")
        except ServiceError as exc:
            st.error(str(exc))
    st.stop()

try:
    identity=api("GET","/auth/me")
    conversations=api("GET","/conversations")
except ServiceError as exc:
    show_failure(exc)
    if st.button("Reintentar conexión"):
        st.rerun()
    if st.button("Volver al inicio de sesión"):
        end_session();st.rerun()
    st.stop()

st.session_state.chatpnl_user=identity["username"]
with st.sidebar:
    st.title("Mis conversaciones")
    st.write("Sesión:",identity["username"])
    if st.button("Cerrar sesión"):
        end_session();st.rerun()
    if st.button("Nueva conversación"):
        try:
            item=api("POST","/conversations",json={"title":"Nueva conversación"})
            st.session_state.chatpnl_active=item["id"]
            st.session_state.pop("chatpnl_pending",None)
            st.rerun()
        except ServiceError as exc:
            show_failure(exc)
    if st.button("Actualizar historial"):
        st.rerun()

if not conversations:
    st.write("Todavía no tienes conversaciones. Pulsa Nueva conversación para comenzar.")
    st.stop()

ids=[item["id"] for item in conversations]
if st.session_state.get("chatpnl_active") not in ids:
    st.session_state.chatpnl_active=ids[0]
labels={item["id"]:f"{item['title']} (#{item['id']})" for item in conversations}
# El dato de selección se conserva aunque cambien los títulos del selector.
st.session_state.chatpnl_choice=st.session_state.chatpnl_active
with st.sidebar:
    selected=st.selectbox("Conversaciones",ids,key="chatpnl_choice",format_func=lambda cid:labels[cid],on_change=select_history)
    conversation=next(item for item in conversations if item["id"]==selected)
    with st.form("chatpnl_rename",clear_on_submit=True):
        title=st.text_input("Nuevo título",max_chars=120)
        renamed=st.form_submit_button("Renombrar")
    if renamed:
        try:
            api("PATCH",f"/conversations/{selected}",json={"title":title})
            st.rerun()
        except ServiceError as exc:
            show_failure(exc)
    confirmed=st.checkbox("Confirmo eliminar esta conversación",key=f"delete_confirmation_{selected}")
    if st.button("Eliminar conversación",disabled=not confirmed):
        try:
            api("DELETE",f"/conversations/{selected}")
            st.session_state.pop("chatpnl_active",None)
            st.session_state.pop("chatpnl_pending",None)
            st.rerun()
        except ServiceError as exc:
            show_failure(exc)

st.subheader(conversation["title"])
st.caption("Los mensajes y las fuentes se recuperan de MySQL para la cuenta autenticada.")
try:
    messages=api("GET",f"/conversations/{selected}/messages")
except ServiceError as exc:
    show_failure(exc);st.stop()
for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        for ref in message.get("references",[]):
            st.caption(f"Fuente: {ref['source']}, página {ref['page']}, {ref['id']}")

pending=st.session_state.get("chatpnl_pending")
if pending:
    st.warning("No se confirmó el último envío. Reintentar conserva su identificador para evitar mensajes duplicados.")
    if st.button("Reintentar envío"):
        send_turn(pending)
    if st.button("Descartar reintento"):
        st.session_state.pop("chatpnl_pending",None);st.rerun()
if prompt:=st.chat_input("Consulta del reglamento",max_chars=1000,disabled=bool(pending)):
    if prompt.strip():
        pending={"cid":selected,"text":prompt,"request_id":str(uuid.uuid4())}
        st.session_state.chatpnl_pending=pending
        send_turn(pending)
# TODO_ESTUDIANTE: incorporar documentos propios por propietario desde L07.
# TODO_ESTUDIANTE: integrar intenciones, entidades y comparación clásica/contextual con evaluación propia.
