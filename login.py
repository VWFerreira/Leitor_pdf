import streamlit as st

usuarios = {
    "user 1": "7eKd92Lm",
    "user 2": "fP3xZq1R",
    "user 3": "Yt9N4s8V",
    "user 4": "qJ6zLmST",
    "user 5": "Wm82Rg7A",
    "user 6": "Dt17Xp9L",
    "user 7": "AkSQw9D",
    "user 8": "Ns49Mt2J",
    "user 9": "Lv30Hr6C",
    "user 10": "12345"
}

def exibir_login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.image("img/logo1.png", width=160)
        st.title("Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if usuario in usuarios and usuarios[usuario] == senha:
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
