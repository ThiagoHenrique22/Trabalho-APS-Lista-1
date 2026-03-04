import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
from datetime import datetime

# =============================
# CONFIGURAÇÃO INICIAL
# =============================

st.set_page_config(page_title="Comanda Eletrônica", layout="wide")

# =============================
# BANCO DE DADOS
# =============================

conn = sqlite3.connect("comanda.db", check_same_thread=False)
cursor = conn.cursor()

# Tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
""")

# Tabela de comandas
cursor.execute("""
CREATE TABLE IF NOT EXISTS comanda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numeracao_comanda TEXT,
    nome_produto TEXT,
    valor_produto REAL,
    quantidade_produto INTEGER,
    valor_total REAL,
    data_registro TEXT
)
""")

conn.commit()

# =============================
# FUNÇÕES
# =============================

def criar_usuario(username, senha):
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    try:
        cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)",
                       (username, senha_hash))
        conn.commit()
        return True
    except:
        return False

def verificar_login(username, senha):
    cursor.execute("SELECT senha FROM usuarios WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    if resultado:
        return bcrypt.checkpw(senha.encode(), resultado[0])
    return False

def adicionar_item(numeracao, nome, valor, quantidade):
    total = valor * quantidade
    cursor.execute("""
        INSERT INTO comanda 
        (numeracao_comanda, nome_produto, valor_produto, quantidade_produto, valor_total, data_registro)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (numeracao, nome, valor, quantidade, total, datetime.now()))
    conn.commit()

def listar_itens(numeracao):
    cursor.execute("SELECT nome_produto, valor_produto, quantidade_produto, valor_total FROM comanda WHERE numeracao_comanda = ?", (numeracao,))
    return cursor.fetchall()

def calcular_total_comanda(numeracao):
    cursor.execute("SELECT SUM(valor_total) FROM comanda WHERE numeracao_comanda = ?", (numeracao,))
    total = cursor.fetchone()[0]
    return total if total else 0

# =============================
# CONTROLE DE SESSÃO
# =============================

if "logado" not in st.session_state:
    st.session_state.logado = False

# =============================
# TELA DE LOGIN
# =============================

if not st.session_state.logado:

    st.title("🔐 Login - Comanda Eletrônica")

    opcao = st.radio("Escolha:", ["Login", "Cadastrar"])

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if opcao == "Cadastrar":
        if st.button("Cadastrar"):
            if criar_usuario(username, senha):
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.error("Usuário já existe!")

    if opcao == "Login":
        if st.button("Entrar"):
            if verificar_login(username, senha):
                st.session_state.logado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

# =============================
# SISTEMA PRINCIPAL
# =============================

else:

    st.title("🧾 Gestão de Comanda Eletrônica")

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.divider()

    st.subheader("➕ Adicionar Item à Comanda")

    numeracao = st.text_input("Número da Comanda")
    nome_produto = st.text_input("Nome do Produto")
    valor_produto = st.number_input("Valor do Produto (R$)", min_value=0.0, format="%.2f")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)

    if st.button("Adicionar Item"):
        if numeracao and nome_produto:
            adicionar_item(numeracao, nome_produto, valor_produto, quantidade)
            st.success("Item adicionado com sucesso!")
        else:
            st.warning("Preencha todos os campos!")

    st.divider()

    st.subheader("📋 Visualizar Comanda")

    consulta_comanda = st.text_input("Digite o número da comanda para visualizar")

    if st.button("Buscar Comanda"):
        itens = listar_itens(consulta_comanda)

        if itens:
            st.write("### Itens da Comanda")
            for item in itens:
                st.write(f"Produto: {item[0]}")
                st.write(f"Valor Unitário: R$ {item[1]:.2f}")
                st.write(f"Quantidade: {item[2]}")
                st.write(f"Total do Item: R$ {item[3]:.2f}")
                st.write("---")

            total_geral = calcular_total_comanda(consulta_comanda)

            st.markdown("## 💰 Total Geral da Compra")
            st.success(f"R$ {total_geral:.2f}")

        else:
            st.warning("Comanda não encontrada ou sem itens.")