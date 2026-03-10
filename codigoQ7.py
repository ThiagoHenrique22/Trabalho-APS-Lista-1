#usuário: amdim
#senha: 1234
import streamlit as st # type: ignore
import hashlib

# ==========================
# Classe Produto
# ==========================
class Produto:

    def __init__(self, nome_produto, unidade_compra, qtd_mes, qtd_compra, preco_estimado):
        self.nome_produto = nome_produto
        self.unidade_compra = unidade_compra
        self.qtd_mes = qtd_mes
        self.qtd_compra = qtd_compra
        self.preco_estimado = preco_estimado
        self.subtotal = self.calcular_subtotal()

    def calcular_subtotal(self):
        return self.qtd_compra * self.preco_estimado

    def atualizar_preco(self, novo_preco):
        self.preco_estimado = novo_preco
        self.subtotal = self.calcular_subtotal()

    def alterar_qtd_compra(self, nova_qtd):
        self.qtd_compra = nova_qtd
        self.subtotal = self.calcular_subtotal()


# ==========================
# Classe ListaCompra
# ==========================
class ListaCompra:

    def __init__(self, mes, ano):
        self.mes = mes
        self.ano = ano
        self.produtos = []
        self.total_compra = 0

    def adicionar_produto(self, produto):
        self.produtos.append(produto)
        self.calcular_total_compra()

    def remover_produto(self, nome):
        self.produtos = [p for p in self.produtos if p.nome_produto != nome]
        self.calcular_total_compra()

    def listar_produtos(self):
        return self.produtos

    def calcular_total_compra(self):
        self.total_compra = sum(p.subtotal for p in self.produtos)
        return self.total_compra


# ==========================
# Função de criptografia
# ==========================
def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# ==========================
# Usuário padrão
# ==========================
usuario = "admin"
senha_hash = criptografar_senha("1234")


# ==========================
# Controle de sessão
# ==========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "lista" not in st.session_state:
    st.session_state.lista = ListaCompra("Maio", 2026)


# ==========================
# Tela de Login
# ==========================
if not st.session_state.logado:

    st.title("Login do Sistema")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == usuario and criptografar_senha(senha) == senha_hash:
            st.session_state.logado = True
            st.success("Login realizado com sucesso")
        else:
            st.error("Usuário ou senha incorretos")

else:

    st.title("Lista de Compras Mensal")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Cadastrar Produto", "Listar Produtos", "Remover Produto"]
    )

    lista = st.session_state.lista


# ==========================
# Cadastro Produto
# ==========================
    if menu == "Cadastrar Produto":

        st.subheader("Cadastrar Produto")

        nome = st.text_input("Nome do Produto")

        unidade = st.selectbox(
            "Unidade de Compra",
            ["kg", "g", "unidade", "litro"]
        )

        qtd_mes = st.number_input("Quantidade prevista para o mês", min_value=0.0)

        qtd_compra = st.number_input("Quantidade que será comprada", min_value=0.0)

        preco = st.number_input("Preço estimado", min_value=0.0)

        if st.button("Adicionar Produto"):

            produto = Produto(nome, unidade, qtd_mes, qtd_compra, preco)

            lista.adicionar_produto(produto)

            st.success("Produto adicionado com sucesso!")


# ==========================
# Listar Produtos
# ==========================
    elif menu == "Listar Produtos":

        st.subheader("Produtos da Lista")

        produtos = lista.listar_produtos()

        if produtos:

            for p in produtos:

                st.write(f"Produto: {p.nome_produto}")
                st.write(f"Unidade: {p.unidade_compra}")
                st.write(f"Qtd Mês: {p.qtd_mes}")
                st.write(f"Qtd Compra: {p.qtd_compra}")
                st.write(f"Preço: R$ {p.preco_estimado}")
                st.write(f"Subtotal: R$ {p.subtotal}")
                st.write("--------------------------")

            total = lista.calcular_total_compra()

            st.subheader(f"Total da Compra: R$ {total}")

        else:
            st.warning("Nenhum produto cadastrado")


# ==========================
# Remover Produto
# ==========================
    elif menu == "Remover Produto":

        st.subheader("Remover Produto")

        nomes = [p.nome_produto for p in lista.listar_produtos()]

        if nomes:

            nome_remover = st.selectbox("Escolha o produto", nomes)

            if st.button("Remover"):
                lista.remover_produto(nome_remover)
                st.success("Produto removido")

        else:

            st.warning("Nenhum produto para remover")
