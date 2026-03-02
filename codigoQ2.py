import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore

# -------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------

st.set_page_config(page_title="Configuração de Texto", layout="centered")

# -------------------------
# CONTROLE DE SESSÃO
# -------------------------

if "logado" not in st.session_state:
    st.session_state.logado = False

# -------------------------
# BANCO DE DADOS
# -------------------------

conn = sqlite3.connect("texto_app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha BLOB
)
""")

conn.commit()

# -------------------------
# ENUMS (conforme UML)
# -------------------------

enumcor = ["black", "white", "blue", "yellow", "gray"]
enumtipo = ["label", "edit", "memo"]

# -------------------------
# FUNÇÕES DE SEGURANÇA
# -------------------------

def criptografar_senha(senha):
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash)

def cadastrar_usuario(username, senha):
    senha_hash = criptografar_senha(senha)
    try:
        cursor.execute(
            "INSERT INTO usuarios (username, senha) VALUES (?, ?)",
            (username, senha_hash)
        )
        conn.commit()
        return True
    except:
        return False

def login_usuario(username, senha):
    cursor.execute(
        "SELECT senha FROM usuarios WHERE username = ?",
        (username,)
    )
    resultado = cursor.fetchone()
    if resultado:
        return verificar_senha(senha, resultado[0])
    return False

# -------------------------
# INTERFACE
# -------------------------

st.title("Sistema de Configuração de Texto")

menu = ["Login", "Cadastro"]
escolha = st.sidebar.selectbox("Menu", menu)

# -------------------------
# CADASTRO
# -------------------------

if escolha == "Cadastro":

    st.subheader("Cadastro de Usuário")

    novo_user = st.text_input("Usuário")
    nova_senha = st.text_input("Senha", type="password")

    if st.button("Cadastrar"):
        if cadastrar_usuario(novo_user, nova_senha):
            st.success("Usuário cadastrado com sucesso!")
        else:
            st.error("Usuário já existe!")

# -------------------------
# LOGIN
# -------------------------

elif escolha == "Login":

    if not st.session_state.logado:

        st.subheader("Login")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if login_usuario(user, senha):
                st.session_state.logado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    else:

        st.success("Usuário logado!")

        if st.button("Sair"):
            st.session_state.logado = False
            st.rerun()

        st.divider()
        st.header("Configurar Texto")

        texto = st.text_area("Digite o texto")

        tamanho = st.slider("Tamanho da letra", 10, 60, 20)

        cor_fonte = st.selectbox("Cor da Fonte", enumcor)
        cor_fundo = st.selectbox("Cor do Fundo", enumcor)

        tipo_comp = st.selectbox("Tipo de Componente", enumtipo)

        if st.button("Exibir Texto"):

            estilo = f"""
            <div style="
                font-size:{tamanho}px;
                color:{cor_fonte};
                background-color:{cor_fundo};
                padding:10px;
                border-radius:5px;">
                {texto}
            </div>
            """

            if tipo_comp == "label":
                st.markdown(estilo, unsafe_allow_html=True)

            elif tipo_comp == "edit":
                st.text_input("Edit", value=texto)

            elif tipo_comp == "memo":
                st.text_area("Memo", value=texto, height=150)