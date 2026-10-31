import streamlit as st
from chatpnl_labs.core import Retriever, corpus, answer
st.set_page_config(page_title="ChatPNL · TF-IDF",layout="wide")
st.title("Buscar evidencia con TF-IDF")
st.caption("El coseno ordena similitud léxica; no es probabilidad de corrección. Se exige cobertura de todos los términos relevantes de la pregunta; el umbral se ajusta solo con desarrollo.")
query=st.text_input("Consulta",value="cuántos libros puedo pedir")
k=st.slider("Top-k",1,4,3)
threshold=st.slider("Umbral didáctico de abstención",0.0,1.0,0.08,0.01)
retriever=Retriever(corpus())
if query.strip():
    st.dataframe(retriever.search(query,k),use_container_width=True)
    st.json(answer(query,retriever,threshold))
# TODO_ESTUDIANTE: comparar k, unigramas/bigramas y consultas sin evidencia.
