import streamlit as st # type: ignore
import sqlite3
import hashlib
from datetime import datetime

# ==============================
# BANCO DE DADOS
# ==============================

conn = sqlite3.connect("colecao_cd.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabelas
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cantor_ou_conjunto TEXT,
    titulo_cd TEXT,
    ano_lancamento INTEGER,
    username TEXT
)
""")

conn.commit()

# ==============================
# FUNÇÃO CRIPTOGRAFIA
# ==============================

def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ==============================
# LOGIN
# ==============================

def tela_login():
    st.title("🎵 Sistema de Coleção de CD's - Palm-top")

    opcao = st.radio("Escolha uma opção:", ["Login", "Cadastrar"])

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if opcao == "Cadastrar":
        if st.button("Criar Conta"):
            senha_hash = criptografar_senha(senha)
            try:
                cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, senha_hash))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except:
                st.error("Usuário já existe.")

    else:
        if st.button("Entrar"):
            senha_hash = criptografar_senha(senha)
            cursor.execute("SELECT * FROM usuarios WHERE username=? AND senha=?", (username, senha_hash))
            user = cursor.fetchone()
            if user:
                st.session_state["logado"] = True
                st.session_state["usuario"] = username
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# ==============================
# SISTEMA PRINCIPAL
# ==============================

def sistema():
    st.title("📀 Gestão de Coleção de CD's")

    st.subheader("Cadastrar novo CD")

    cantor = st.text_input("Nome do Cantor(a) ou Conjunto")
    titulo = st.text_input("Título do CD")
    ano = st.number_input("Ano de Lançamento", min_value=1900, max_value=datetime.now().year, step=1)

    if st.button("Cadastrar CD"):
        if cantor and titulo:
            cursor.execute("""
            INSERT INTO cds (cantor_ou_conjunto, titulo_cd, ano_lancamento, username)
            VALUES (?, ?, ?, ?)
            """, (cantor, titulo, ano, st.session_state["usuario"]))
            conn.commit()
            st.success("CD cadastrado no Palm-top com sucesso!")
            st.rerun()
        else:
            st.warning("Preencha todos os campos.")

    st.divider()

    st.subheader("📂 Coleções Agrupadas no Palm-top")

    cursor.execute("""
    SELECT cantor_ou_conjunto, titulo_cd, ano_lancamento 
    FROM cds WHERE username=? 
    ORDER BY cantor_ou_conjunto
    """, (st.session_state["usuario"],))

    cds = cursor.fetchall()

    if cds:
        colecao = {}
        for cd in cds:
            cantor = cd[0]
            if cantor not in colecao:
                colecao[cantor] = []
            colecao[cantor].append((cd[1], cd[2]))

        for cantor, lista in colecao.items():
            with st.expander(f"🎤 {cantor}"):
                for titulo, ano in lista:
                    st.write(f"📀 {titulo} ({ano})")
    else:
        st.info("Nenhum CD cadastrado.")

    st.divider()

    if st.button("Logout"):
        st.session_state["logado"] = False
        st.rerun()


# ==============================
# CONTROLE DE SESSÃO
# ==============================

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if st.session_state["logado"]:
    sistema()
else:
    tela_login()