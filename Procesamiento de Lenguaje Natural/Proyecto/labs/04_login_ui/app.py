import streamlit as st
st.set_page_config(page_title="ChatPNL · simulación")
st.title("Formularios de acceso")
st.error("SIMULACIÓN NO SEGURA. No valida identidad. No escribas contraseñas reales; aquí no se solicitan.")
mode=st.radio("Vista",["Registro de demostración","Entrada de demostración"])
if not st.session_state.get("demo_user"):
    with st.form("demo"):
        alias=st.text_input("Alias ficticio")
        consent=st.checkbox("Comprendo que solo simula la interfaz")
        if st.form_submit_button("Continuar"):
            if len(alias.strip())<3 or not consent: st.error("Escribe al menos tres caracteres y confirma la simulación")
            else: st.session_state.demo_user=alias.strip();st.rerun()
else:
    st.success("Vista privada simulada para "+st.session_state.demo_user)
    st.info("La autorización real se hará en FastAPI en el L06; ocultar este panel no protege recursos.")
    if st.button("Cerrar sesión"):
        del st.session_state.demo_user;st.rerun()
# TODO_ESTUDIANTE: validar alias alfanumérico, mostrar errores específicos, añadir una sección condicional.
