import uuid
import streamlit as st
from chatpnl_labs.core import deterministic_reply
st.set_page_config(page_title="ChatPNL · historial",page_icon="💬",layout="wide")
def new_conversation():
    cid=str(uuid.uuid4())
    st.session_state.conversations[cid]={"title":"Nueva conversación","messages":[]}
    st.session_state.active=cid
def select_conversation():
    st.session_state.active=st.session_state.conversation_choice
def delete_active_conversation():
    del st.session_state.conversations[st.session_state.active]
    if st.session_state.conversations:
        st.session_state.active=next(iter(st.session_state.conversations))
    else:
        new_conversation()
if "conversations" not in st.session_state: st.session_state.conversations={}
if not st.session_state.conversations: new_conversation()
with st.sidebar:
    st.title("ChatPNL")
    st.button("Nueva conversación",on_click=new_conversation)
    ids=list(st.session_state.conversations)
    titles={cid:f'{st.session_state.conversations[cid]["title"]} ({cid[:8]})' for cid in ids}
    # Separar la selección del widget del dato persistente evita perderla al renombrar.
    st.session_state.conversation_choice=st.session_state.active
    selected=st.selectbox("Conversaciones",ids,key="conversation_choice",format_func=lambda x:titles[x],on_change=select_conversation)
    with st.form("rename"):
        title=st.text_input("Nuevo título")
        if st.form_submit_button("Renombrar") and title.strip():
            st.session_state.conversations[selected]["title"]=title.strip();st.rerun()
    st.button("Eliminar conversación",on_click=delete_active_conversation)
conv=st.session_state.conversations[st.session_state.active]
st.title(conv["title"])
st.warning("Historial temporal: cerrar o perder la sesión puede borrar los datos. No sustituye una base de datos.")
for m in conv["messages"]:
    with st.chat_message(m["role"]): st.write(m["content"])
if prompt:=st.chat_input("Pregunta",max_chars=1000):
    if prompt.strip():
        conv["messages"].extend([{"role":"user","content":prompt},{"role":"assistant","content":deterministic_reply(prompt)}]);st.rerun()
# TODO_ESTUDIANTE: títulos automáticos, búsqueda por texto y confirmación antes de eliminar.
