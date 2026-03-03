import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
from enum import Enum
import time

# ==============================
# ENUM DE DIREÇÃO
# ==============================
class EnumDirecao(str, Enum):
    CIMA = "cima"
    BAIXO = "baixo"
    DIREITA = "direita"
    ESQUERDA = "esquerda"


# ==============================
# CONEXÃO COM BANCO
# ==============================
def conectar():
    return sqlite3.connect("sistema.db", check_same_thread=False)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonecos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            coord_x INTEGER,
            coord_y INTEGER,
            posicao TEXT,
            usuario_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()


# ==============================
# FUNÇÕES DE USUÁRIO
# ==============================
def criar_usuario(username, password):
    conn = conectar()
    cursor = conn.cursor()

    senha_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            (username, senha_hash)
        )
        conn.commit()
        st.success("Usuário criado com sucesso!")
    except:
        st.error("Usuário já existe!")

    conn.close()


def autenticar(username, password):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, password FROM usuarios WHERE username = ?",
        (username,)
    )
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        user_id, senha_hash = usuario
        if bcrypt.checkpw(password.encode(), senha_hash):
            return user_id
    return None


# ==============================
# FUNÇÕES DO BONECO
# ==============================
def salvar_boneco(nome, x, y, direcao, usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bonecos (nome, coord_x, coord_y, posicao, usuario_id)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, x, y, direcao, usuario_id))

    conn.commit()
    conn.close()


def listar_bonecos(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, coord_x, coord_y, posicao
        FROM bonecos
        WHERE usuario_id = ?
    """, (usuario_id,))

    dados = cursor.fetchall()
    conn.close()
    return dados


# ==============================
# INÍCIO DA APLICAÇÃO
# ==============================
criar_tabelas()

st.set_page_config(page_title="Gerenciador de Boneco")

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None


# ==============================
# LOGIN
# ==============================
if st.session_state.usuario_id is None:

    st.title("Login")

    aba = st.radio("Escolha:", ["Entrar", "Cadastrar"])

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if aba == "Cadastrar":
        if st.button("Criar Conta"):
            criar_usuario(username, password)

    if aba == "Entrar":
        if st.button("Login"):
            user_id = autenticar(username, password)
            if user_id:
                st.session_state.usuario_id = user_id
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")


# ==============================
# SISTEMA PRINCIPAL
# ==============================
else:
    inicio = time.time()  # Controle de desempenho

    st.title("Gerenciamento de Posição do Boneco")

    if st.button("Logout"):
        st.session_state.usuario_id = None
        st.rerun()

    st.subheader("Cadastrar Novo Boneco")

    nome = st.text_input("Nome do Boneco")
    x = st.number_input("Coordenada X", step=1)
    y = st.number_input("Coordenada Y", step=1)
    direcao = st.selectbox(
        "Direção",
        [e.value for e in EnumDirecao]
    )

    if st.button("Salvar Boneco"):
        salvar_boneco(nome, int(x), int(y), direcao, st.session_state.usuario_id)
        st.success("Boneco salvo com sucesso!")
        st.rerun()

    st.subheader("Bonecos Cadastrados")

    dados = listar_bonecos(st.session_state.usuario_id)

    for b in dados:
        st.write(f"Nome: {b[0]} | X: {b[1]} | Y: {b[2]} | Direção: {b[3]}")

    # ==============================
    # RNF002 - Controle simples de desempenho
    # ==============================
    tempo_execucao = time.time() - inicio
    if tempo_execucao > 2:
        st.warning("Tempo de resposta acima do esperado!")