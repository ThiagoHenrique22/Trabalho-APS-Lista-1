import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
from datetime import datetime

# ===============================
# CONFIGURAÇÃO DO BANCO
# ===============================

def conectar():
    return sqlite3.connect("lista_compras.db", check_same_thread=False)

conn = conectar()
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
CREATE TABLE IF NOT EXISTS lista_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_produto TEXT,
    unidade_compra TEXT,
    quantidade_mes REAL,
    quantidade_comprada REAL,
    preco_estimado REAL
)
""")
conn.commit()

# ===============================
# FUNÇÕES DE SEGURANÇA
# ===============================

def criptografar_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash)

# ===============================
# FUNÇÕES CRUD
# ===============================

def adicionar_produto(nome, unidade, q_mes, q_comp, preco):
    cursor.execute("""
        INSERT INTO lista_compra 
        (nome_produto, unidade_compra, quantidade_mes, quantidade_comprada, preco_estimado)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, unidade, q_mes, q_comp, preco))
    conn.commit()

def listar_produtos():
    cursor.execute("SELECT * FROM lista_compra")
    return cursor.fetchall()

def calcular_total():
    cursor.execute("SELECT SUM(preco_estimado * quantidade_comprada) FROM lista_compra")
    total = cursor.fetchone()[0]
    return total if total else 0

# ===============================
# CONTROLE DE LOGIN
# ===============================

if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_login():
    st.title("🔐 Login - Lista de Compras")

    aba = st.radio("Escolha:", ["Login", "Cadastrar"])

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if aba == "Cadastrar":
        if st.button("Cadastrar"):
            senha_hash = criptografar_senha(senha)
            try:
                cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", 
                               (username, senha_hash))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except:
                st.error("Usuário já existe!")

    if aba == "Login":
        if st.button("Entrar"):
            cursor.execute("SELECT senha FROM usuarios WHERE username = ?", (username,))
            resultado = cursor.fetchone()
            if resultado and verificar_senha(senha, resultado[0]):
                st.session_state.logado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

# ===============================
# TELA PRINCIPAL
# ===============================

def tela_principal():
    st.title("🛒 Gestão de Lista de Compras")

    with st.form("form_produto"):
        st.subheader("Adicionar Produto")

        nome = st.text_input("Nome do Produto")
        unidade = st.selectbox("Unidade Comprada", ["kg", "g"])
        quantidade_mes = st.number_input("Quantidade para um mês", min_value=0.0, step=0.1)
        quantidade_comprada = st.number_input("Quantidade Comprada", min_value=0.0, step=0.1)
        preco = st.number_input("Preço Estimado (R$)", min_value=0.0, step=0.1)

        submitted = st.form_submit_button("Adicionar")

        if submitted:
            adicionar_produto(nome, unidade, quantidade_mes, quantidade_comprada, preco)
            st.success("Produto adicionado com sucesso!")
            st.rerun()

    st.divider()

    st.subheader("📋 Lista de Produtos")

    produtos = listar_produtos()

    if produtos:
        for p in produtos:
            st.write(f"""
            **Produto:** {p[1]}  
            Unidade: {p[2]}  
            Qtd/Mês: {p[3]}  
            Qtd Comprada: {p[4]}  
            Preço: R$ {p[5]:.2f}  
            ---
            """)
    else:
        st.info("Nenhum produto cadastrado.")

    st.divider()

    total = calcular_total()
    st.subheader(f"💰 Total da Compra: R$ {total:.2f}")

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# ===============================
# EXECUÇÃO
# ===============================

if not st.session_state.logado:
    tela_login()
else:
    tela_principal()