import streamlit as st
import mysql.connector

# Função para verificar o login no MySQL
def verificar_login(usuario, senha):
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",  
            password="13312208",
            database="app_pdf"
        )
        cursor = conexao.cursor()
        consulta = "SELECT * FROM usuarios WHERE usuario=%s AND senha=%s"
        cursor.execute(consulta, (usuario, senha))
        resultado = cursor.fetchone()
        conexao.close()
        return resultado is not None
    except:
        return False

# Interface de login
def exibir_login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.image("img/logo1.png", width=160)
        st.title("Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if verificar_login(usuario, senha):
                st.session_state.autenticado = True
                st.success("Login realizado com sucesso!")
                st.rerun()

            else:
                st.error("Usuário ou senha incorretos")

        st.markdown(
            """
            <hr style="margin-top: 50px; margin-bottom:10px; border: 1px solid #444;">
            <div style="text-align: center; color: gray; font-size: 14px;">
                By Vilmar William Ferreira • © 2025
            </div>
            """,
            unsafe_allow_html=True
        )

        st.stop()

# Executar login se rodar diretamente
if __name__ == "__main__":
    exibir_login()