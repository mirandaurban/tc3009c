import streamlit as st
st.set_page_config(page_title="ChatPNL · componentes",page_icon="📚",layout="wide")
st.title("Un perfil para explorar Streamlit")
st.markdown("Cada interacción **vuelve a ejecutar** este archivo. El formulario envía sus campos juntos.")
with st.sidebar:
    st.header("Preferencias")
    topic=st.selectbox("Tema",["Biblioteca","Programación","Investigación"])
    show=st.checkbox("Mostrar explicación",value=True)
    hours=st.slider("Horas de estudio",1,10,3)
with st.form("profile"):
    name=st.text_input("Alias de práctica (sin datos personales)")
    sent=st.form_submit_button("Guardar perfil")
if sent:
    if not name.strip(): st.error("El alias es obligatorio")
    else: st.session_state.profile_data={"alias":name.strip(),"tema":topic,"horas":hours}
left,right=st.columns(2)
with left:
    st.subheader("Datos enviados")
    st.write(st.session_state.get("profile_data", "Aún no hay perfil"))
with right:
    if show: st.info("Una variable local se reconstruye; session_state conserva datos mientras vive esta sesión.")
if st.button("Contar clic"):
    st.session_state.clicks=st.session_state.get("clicks",0)+1
st.write("Clics:",st.session_state.get("clicks",0))
# TODO_ESTUDIANTE: añadir carrera, validar campos y organizar una ficha de perfil.
