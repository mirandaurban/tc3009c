import streamlit as st
from chatpnl_labs.core import deterministic_reply
st.set_page_config(page_title="ChatPNL · chat",page_icon="💬")
st.title("ChatPNL · mi primer chat")
st.caption("Respuestas deterministas locales; sin modelo generativo.")
if "messages" not in st.session_state: st.session_state.messages=[]
if st.sidebar.button("Limpiar conversación"):
    st.session_state.messages=[]
    st.rerun()
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.write(message["content"])
if prompt:=st.chat_input("Escribe una pregunta",max_chars=1000):
    if prompt.strip():
        st.session_state.messages.extend([{"role":"user","content":prompt},{"role":"assistant","content":deterministic_reply(prompt)}])
        st.rerun()
# TODO_ESTUDIANTE: mensaje de bienvenida, validación de longitud propia y reinicio con bienvenida.
