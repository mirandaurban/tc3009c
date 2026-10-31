import os
from dotenv import load_dotenv
import streamlit as st
from chatpnl_labs.core import Retriever, corpus
from chatpnl_labs.semantic import load_encoder, semantic_search
load_dotenv()
st.set_page_config(page_title="ChatPNL · dos recuperadores",layout="wide")
st.title("TF-IDF frente a embeddings")
query=st.text_input("Consulta",value="quiero llevar libros a casa")
chunks=corpus()
left,right=st.columns(2)
if query.strip():
    with left:
        st.subheader("TF-IDF")
        st.dataframe(Retriever(chunks).search(query),use_container_width=True)
    with right:
        st.subheader("MiniLM multilingüe · CPU")
        try:
            if "encoder" not in st.session_state:
                with st.spinner("Cargando modelo local..."):
                    st.session_state.encoder=load_encoder(os.getenv("CHATPNL_MODEL_PATH"))
            st.dataframe(semantic_search(st.session_state.encoder,chunks,query),use_container_width=True)
        except (OSError,ImportError,ValueError) as exc:
            st.warning("Contextual pendiente. Prepare el modelo local según docs/MODELO.md. TF-IDF sigue disponible.")
# TODO_ESTUDIANTE: analizar desacuerdos, Recall@3 y MRR@5; no comparar cosenos como probabilidades.
