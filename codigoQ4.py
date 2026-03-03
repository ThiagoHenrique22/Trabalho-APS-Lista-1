import streamlit as st # type: ignore
import sqlite3
import bcrypt # type: ignore
import pandas as pd # type: ignore
from datetime import datetime, timedelta
import time

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Sistema Clínica", layout="wide")

# ==============================
# BANCO DE DADOS
# ==============================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("clinica.db", check_same_thread=False)
    return conn

conn = get_connection()
cursor = conn.cursor()

def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paciente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        endereco TEXT,
        data_inicio_remedio DATE,
        duracao_remedio INTEGER,
        vezes_dia INTEGER,
        dosagem REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        crm INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS remedio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        num_serie TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atendimento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        medico_id INTEGER,
        data_atendimento DATETIME,
        observacao TEXT
    )
    """)

    conn.commit()

create_tables()

# ==============================
# SEGURANÇA (RNF001)
# ==============================

def hash_senha(senha):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode(), salt)

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash)

# ==============================
# LOGIN
# ==============================

def tela_login():
    st.title("🔐 Login")

    opcao = st.radio("Escolha:", ["Login", "Cadastrar"])

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if opcao == "Cadastrar":
        if st.button("Criar Conta"):
            try:
                senha_hash = hash_senha(senha)
                cursor.execute("INSERT INTO usuario (username, senha) VALUES (?, ?)",
                               (username, senha_hash))
                conn.commit()
                st.success("Usuário criado com sucesso!")
            except:
                st.error("Usuário já existe.")

    if opcao == "Login":
        if st.button("Entrar"):
            cursor.execute("SELECT senha FROM usuario WHERE username=?", (username,))
            result = cursor.fetchone()
            if result and verificar_senha(senha, result[0]):
                st.session_state["logado"] = True
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

# ==============================
# CRUD PACIENTE (RF001)
# ==============================

def gerenciar_paciente():
    st.header("👤 Gerenciar Paciente")

    with st.form("form_paciente"):
        nome = st.text_input("Nome")
        endereco = st.text_input("Endereço")
        data_inicio = st.date_input("Data início remédio")
        duracao = st.number_input("Duração (dias)", min_value=1)
        vezes_dia = st.number_input("Vezes ao dia", min_value=1)
        dosagem = st.number_input("Dosagem", min_value=0.1)

        submitted = st.form_submit_button("Salvar")

        if submitted:
            cursor.execute("""
            INSERT INTO paciente (nome, endereco, data_inicio_remedio,
            duracao_remedio, vezes_dia, dosagem)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (nome, endereco, data_inicio, duracao, vezes_dia, dosagem))
            conn.commit()
            st.success("Paciente cadastrado!")

    df = pd.read_sql("SELECT * FROM paciente", conn)
    st.dataframe(df)

# ==============================
# CRUD MEDICO (RF002)
# ==============================

def gerenciar_medico():
    st.header("🩺 Gerenciar Médico")

    with st.form("form_medico"):
        nome = st.text_input("Nome")
        crm = st.number_input("CRM", min_value=1)

        submitted = st.form_submit_button("Salvar")

        if submitted:
            cursor.execute("INSERT INTO medico (nome, crm) VALUES (?, ?)",
                           (nome, crm))
            conn.commit()
            st.success("Médico cadastrado!")

    df = pd.read_sql("SELECT * FROM medico", conn)
    st.dataframe(df)

# ==============================
# CRUD REMEDIO (RF003)
# ==============================

def gerenciar_remedio():
    st.header("💊 Gerenciar Remédio")

    with st.form("form_remedio"):
        nome = st.text_input("Nome")
        num_serie = st.text_input("Número de Série")

        submitted = st.form_submit_button("Salvar")

        if submitted:
            cursor.execute("INSERT INTO remedio (nome, num_serie) VALUES (?, ?)",
                           (nome, num_serie))
            conn.commit()
            st.success("Remédio cadastrado!")

    df = pd.read_sql("SELECT * FROM remedio", conn)
    st.dataframe(df)

# ==============================
# GERAR PLANILHA (RF004)
# ==============================

def gerar_planilha():
    st.header("📅 Gerar Planilha de Horários")

    pacientes = pd.read_sql("SELECT * FROM paciente", conn)

    if pacientes.empty:
        st.warning("Nenhum paciente cadastrado.")
        return

    paciente_id = st.selectbox("Selecione o paciente",
                                pacientes["id"])

    if st.button("Gerar Planilha"):
        p = pacientes[pacientes["id"] == paciente_id].iloc[0]

        horarios = []
        inicio = datetime.strptime(str(p["data_inicio_remedio"]), "%Y-%m-%d")

        for dia in range(p["duracao_remedio"]):
            for vez in range(p["vezes_dia"]):
                horario = inicio + timedelta(days=dia, hours=vez*(24/p["vezes_dia"]))
                horarios.append([p["nome"], horario, p["dosagem"]])

        df = pd.DataFrame(horarios,
                          columns=["Paciente", "Horário", "Dosagem"])

        df.to_excel("planilha_horarios.xlsx", index=False)

        st.success("Planilha gerada!")
        st.download_button("Baixar Planilha",
                           data=open("planilha_horarios.xlsx", "rb"),
                           file_name="planilha_horarios.xlsx")

# ==============================
# ATENDIMENTO (RF005)
# ==============================

def realizar_atendimento():
    st.header("🏥 Realizar Atendimento")

    pacientes = pd.read_sql("SELECT * FROM paciente", conn)
    medicos = pd.read_sql("SELECT * FROM medico", conn)

    if pacientes.empty or medicos.empty:
        st.warning("Cadastre paciente e médico primeiro.")
        return

    paciente_id = st.selectbox("Paciente", pacientes["id"])
    medico_id = st.selectbox("Médico", medicos["id"])
    obs = st.text_area("Observação")

    if st.button("Registrar Atendimento"):
        cursor.execute("""
        INSERT INTO atendimento (paciente_id, medico_id,
        data_atendimento, observacao)
        VALUES (?, ?, ?, ?)
        """, (paciente_id, medico_id, datetime.now(), obs))
        conn.commit()
        st.success("Atendimento registrado!")

    df = pd.read_sql("SELECT * FROM atendimento", conn)
    st.dataframe(df)

# ==============================
# MENU PRINCIPAL
# ==============================

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
else:
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox("Escolha",
                                 ["Paciente",
                                  "Médico",
                                  "Remédio",
                                  "Planilha",
                                  "Atendimento"])

    inicio = time.time()

    if opcao == "Paciente":
        gerenciar_paciente()
    elif opcao == "Médico":
        gerenciar_medico()
    elif opcao == "Remédio":
        gerenciar_remedio()
    elif opcao == "Planilha":
        gerar_planilha()
    elif opcao == "Atendimento":
        realizar_atendimento()

    fim = time.time()

    tempo = fim - inicio

    if tempo > 2:
        st.warning("⚠ Tempo de resposta acima do requisito RNF002")

    if st.sidebar.button("Logout"):
        st.session_state["logado"] = False
        st.rerun()