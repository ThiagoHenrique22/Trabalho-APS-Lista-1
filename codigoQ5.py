import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
import pandas as pd # type: ignore
from datetime import datetime

# ==============================
# CONFIGURAÇÃO INICIAL
# ==============================
st.set_page_config(page_title="Relatório de Gastos", layout="wide")

DB_NAME = "gastos.db"

# ==============================
# CONEXÃO COM BANCO
# ==============================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

# ==============================
# CRIAÇÃO DAS TABELAS
# ==============================
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha BLOB
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipo_gasto (
        idtipo INTEGER PRIMARY KEY AUTOINCREMENT,
        descricaotipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gasto (
        idgasto INTEGER PRIMARY KEY AUTOINCREMENT,
        descricaogasto TEXT,
        valorgasto REAL,
        observacao TEXT,
        forma TEXT,
        idtipo INTEGER,
        data DATE,
        FOREIGN KEY (idtipo) REFERENCES tipo_gasto(idtipo)
    )
    """)
    conn.commit()

create_tables()

# ==============================
# FUNÇÕES DE SEGURANÇA
# ==============================
def criar_usuario(username, senha):
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    cursor.execute("INSERT INTO usuario (username, senha) VALUES (?, ?)", (username, senha_hash))
    conn.commit()

def verificar_login(username, senha):
    cursor.execute("SELECT senha FROM usuario WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    if resultado:
        return bcrypt.checkpw(senha.encode(), resultado[0])
    return False

# Cria usuário padrão se não existir
cursor.execute("SELECT * FROM usuario")
if not cursor.fetchall():
    criar_usuario("admin", "1234")

# ==============================
# LOGIN
# ==============================
if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_login():
    st.title("🔐 Login")

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if verificar_login(username, senha):
            st.session_state.logado = True
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

if not st.session_state.logado:
    tela_login()
    st.stop()

# ==============================
# MENU PRINCIPAL
# ==============================
menu = st.sidebar.selectbox(
    "Menu",
    ["Gerenciar Tipo Gasto", "Gerenciar Gasto", "Listar Forma Pagamento", "Relatório Mensal"]
)

# ==============================
# RF001 - GERENCIAR TIPO GASTO
# ==============================
if menu == "Gerenciar Tipo Gasto":
    st.title("📌 Gerenciar Tipo de Gasto")

    descricao = st.text_input("Descrição do Tipo")

    if st.button("Cadastrar Tipo"):
        cursor.execute("INSERT INTO tipo_gasto (descricaotipo) VALUES (?)", (descricao,))
        conn.commit()
        st.success("Tipo cadastrado com sucesso!")
        st.rerun()

    st.subheader("Tipos Cadastrados")
    df = pd.read_sql("SELECT * FROM tipo_gasto", conn)
    st.dataframe(df)

# ==============================
# ENUM FORMA PAGAMENTO (RF003)
# ==============================
FORMAS = ["dinheiro", "cartao credito", "cartao debito", "ticket alimentacao"]

# ==============================
# RF002 - GERENCIAR GASTO
# ==============================
if menu == "Gerenciar Gasto":
    st.title("💰 Gerenciar Gasto")

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    observacao = st.text_area("Observação")
    forma = st.selectbox("Forma de Pagamento", FORMAS)

    tipos = pd.read_sql("SELECT * FROM tipo_gasto", conn)
    if not tipos.empty:
        tipo = st.selectbox("Tipo de Gasto", tipos["descricaotipo"])
        data = st.date_input("Data", datetime.today())

        if st.button("Cadastrar Gasto"):
            idtipo = tipos[tipos["descricaotipo"] == tipo]["idtipo"].values[0]
            cursor.execute("""
            INSERT INTO gasto (descricaogasto, valorgasto, observacao, forma, idtipo, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (descricao, valor, observacao, forma, idtipo, data))
            conn.commit()
            st.success("Gasto cadastrado!")
            st.rerun()
    else:
        st.warning("Cadastre um tipo de gasto primeiro.")

# ==============================
# RF003 - LISTAR FORMAS PAGAMENTO
# ==============================
if menu == "Listar Forma Pagamento":
    st.title("💳 Formas de Pagamento")

    df = pd.DataFrame(FORMAS, columns=["Forma"])
    st.table(df)

# ==============================
# RF004 - RELATÓRIO MENSAL
# ==============================
if menu == "Relatório Mensal":
    st.title("📊 Relatório de Gastos Mensais")

    mes = st.selectbox("Mês", list(range(1, 13)))
    ano = st.number_input("Ano", min_value=2000, max_value=2100, value=datetime.today().year)

    query = f"""
    SELECT g.descricaogasto, g.valorgasto, g.forma, t.descricaotipo, g.data
    FROM gasto g
    JOIN tipo_gasto t ON g.idtipo = t.idtipo
    WHERE strftime('%m', g.data) = '{str(mes).zfill(2)}'
    AND strftime('%Y', g.data) = '{ano}'
    """

    df = pd.read_sql(query, conn)

    if not df.empty:
        st.dataframe(df)
        st.subheader("Total do Mês")
        st.success(f"R$ {df['valorgasto'].sum():.2f}")
    else:
        st.info("Nenhum gasto encontrado para este mês.")