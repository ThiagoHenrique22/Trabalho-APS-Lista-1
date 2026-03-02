import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
from datetime import datetime

# ---------------------------
# Banco de Dados
# ---------------------------

conn = sqlite3.connect("conta_luz.db", check_same_thread=False)
cursor = conn.cursor()

# Tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha BLOB
)
""")

# Tabela conta_luz
cursor.execute("""
CREATE TABLE IF NOT EXISTS conta_luz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dt_leitura TEXT,
    n_leitura INTEGER,
    vlr_gasto REAL,
    valor_pg REAL,
    dt_pag TEXT,
    med_cons REAL
)
""")

conn.commit()

# ---------------------------
# Funções de Segurança
# ---------------------------

def criptografar_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash)

# ---------------------------
# Cadastro/Login
# ---------------------------

def cadastrar_usuario(username, senha):
    senha_hash = criptografar_senha(senha)
    try:
        cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                       (username, senha_hash))
        conn.commit()
        return True
    except:
        return False

def login_usuario(username, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    if resultado:
        return verificar_senha(senha, resultado[0])
    return False

# ---------------------------
# Funções Conta Luz
# ---------------------------

def adicionar_conta(dt_leitura, n_leitura, vlr_gasto, valor_pg, dt_pag):
    med_cons = vlr_gasto  # simplificação
    cursor.execute("""
        INSERT INTO conta_luz 
        (dt_leitura, n_leitura, vlr_gasto, valor_pg, dt_pag, med_cons)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (dt_leitura, n_leitura, vlr_gasto, valor_pg, dt_pag, med_cons))
    conn.commit()

def mes_maior_consumo():
    cursor.execute("""
        SELECT dt_leitura, med_cons 
        FROM conta_luz 
        ORDER BY med_cons DESC 
        LIMIT 1
    """)
    return cursor.fetchone()

def mes_menor_consumo():
    cursor.execute("""
        SELECT dt_leitura, med_cons 
        FROM conta_luz 
        ORDER BY med_cons ASC 
        LIMIT 1
    """)
    return cursor.fetchone()

# ---------------------------
# Interface Streamlit
# ---------------------------

st.title("Sistema de Conta de Luz")

menu = ["Login", "Cadastro"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Cadastro":
    st.subheader("Cadastro de Usuário")
    novo_user = st.text_input("Usuário")
    nova_senha = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        if cadastrar_usuario(novo_user, nova_senha):
            st.success("Usuário cadastrado com sucesso!")
        else:
            st.error("Usuário já existe.")

elif escolha == "Login":
    st.subheader("Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if login_usuario(user, senha):
            st.success("Login realizado com sucesso!")

            menu2 = ["Adicionar Conta", "Maior Consumo", "Menor Consumo"]
            opcao = st.selectbox("Escolha uma opção", menu2)

            if opcao == "Adicionar Conta":
                dt_leitura = st.date_input("Data da Leitura")
                n_leitura = st.number_input("Número da Leitura", min_value=0)
                vlr_gasto = st.number_input("Valor Gasto (Consumo)", min_value=0.0)
                valor_pg = st.number_input("Valor Pago", min_value=0.0)
                dt_pag = st.date_input("Data de Pagamento")

                if st.button("Salvar Conta"):
                    adicionar_conta(
                        dt_leitura.strftime("%Y-%m"),
                        n_leitura,
                        vlr_gasto,
                        valor_pg,
                        dt_pag.strftime("%Y-%m-%d")
                    )
                    st.success("Conta cadastrada!")

            elif opcao == "Maior Consumo":
                resultado = mes_maior_consumo()
                if resultado:
                    st.info(f"Mês de MAIOR consumo: {resultado[0]} | Consumo: {resultado[1]}")
                else:
                    st.warning("Nenhum registro encontrado.")

            elif opcao == "Menor Consumo":
                resultado = mes_menor_consumo()
                if resultado:
                    st.info(f"Mês de MENOR consumo: {resultado[0]} | Consumo: {resultado[1]}")
                else:
                    st.warning("Nenhum registro encontrado.")
        else:
            st.error("Usuário ou senha inválidos.")