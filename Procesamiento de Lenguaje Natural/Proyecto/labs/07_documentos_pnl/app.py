from dataclasses import asdict
import streamlit as st
from chatpnl_labs.core import read_document, chunk_pages
st.set_page_config(page_title="ChatPNL · documentos",layout="wide")
st.title("Del documento a fragmentos con página")
st.caption("Solo material autorizado. Máximo real: 2 MB; PDF con texto o TXT UTF-8. No ejecutamos instrucciones del documento.")
file=st.file_uploader("Documento",type=["pdf","txt"])
size=st.slider("Palabras por fragmento",20,200,90)
overlap=st.slider("Solapamiento en palabras",0,19,15)
if file:
    try:
        with st.status("Extrayendo texto"):
            pages=read_document(file.name,file.getvalue())
            chunks=chunk_pages(file.name,pages,size,overlap)
        st.write("Palabras:",sum(len(t.split()) for _,t in pages))
        st.dataframe([asdict(c) for c in chunks],use_container_width=True)
    except ValueError as exc: st.error(str(exc))
# TODO_ESTUDIANTE: comparar tamaños, resumir cantidad de palabras y filtrar por página.
