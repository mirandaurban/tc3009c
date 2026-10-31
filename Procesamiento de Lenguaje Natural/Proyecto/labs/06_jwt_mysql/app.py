import os
from dotenv import load_dotenv
import streamlit as st
from chatpnl_labs.http_client import request_json, ServiceError
load_dotenv()
st.set_page_config(page_title="ChatPNL · acceso real",page_icon="🔐")
st.title("ChatPNL · JWT y MySQL")
base=os.getenv("CHATPNL_API_URL","http://127.0.0.1:8000")
def call(method,path,**kwargs):
    return request_json(base,method,path,st.session_state.get("token"),**kwargs)
if not st.session_state.get("token"):
    mode=st.radio("Operación",["Iniciar sesión","Registrar usuario"])
    with st.form("credentials",clear_on_submit=True):
        username=st.text_input("Usuario: minúsculas, números o _")
        password=st.text_input("Contraseña de práctica: mínimo 10 caracteres",type="password")
        sent=st.form_submit_button("Enviar")
    if sent:
        try:
            result=call("POST","/auth/login" if mode=="Iniciar sesión" else "/auth/register",json={"username":username,"password":password})
            if "access_token" in result: st.session_state.token=result["access_token"];st.rerun()
            else: st.success("Usuario creado. Ahora inicia sesión.")
        except ServiceError as exc: st.error(str(exc))
else:
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.pop("token",None);st.rerun()
    try:
        st.success("Identidad confirmada por FastAPI")
        st.json(call("GET","/auth/me"))
        with st.form("conversation"):
            title=st.text_input("Título de conversación privada de práctica")
            if st.form_submit_button("Crear conversación"):
                call("POST","/conversations",json={"title":title})
        st.write(call("GET","/conversations"))
    except ServiceError as exc:
        st.error(str(exc))
        if "401" in str(exc): st.session_state.pop("token",None)
st.caption("Token en memoria de sesión, nunca en caché global. Logout borra la copia local: el JWT sigue válido hasta expirar (15 min).")
# TODO_ESTUDIANTE: vista propia de /auth/me, aviso de expiración y prueba sin token con evidencia.
