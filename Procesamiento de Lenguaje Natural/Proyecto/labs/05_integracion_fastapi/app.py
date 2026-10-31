import os
import streamlit as st
from chatpnl_labs.http_client import request_json, ServiceError
st.set_page_config(page_title="ChatPNL · API")
st.title("Del formulario a JSON")
base=os.getenv("CHATPNL_API_URL","http://127.0.0.1:8000")
with st.form("analyze"):
    text=st.text_input("Texto para analizar")
    endpoint=st.selectbox("Operación",["echo","analyze"])
    submitted=st.form_submit_button("Enviar a FastAPI")
if submitted:
    try:
        with st.spinner("Consultando API..."):
            st.json(request_json(base,"POST",f"/api/v1/{endpoint}",json={"text":text}))
    except ServiceError as exc: st.error(str(exc))
st.caption("Envía texto vacío para observar HTTP 422. Detén la API para probar errores de conexión.")
# TODO_ESTUDIANTE: endpoint nuevo, explicar 422 y registrar la recuperación tras una caída.
