
import os
import time
import streamlit as st
import pandas as pd
import plotly.express as px

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==========================================

st.set_page_config(
    page_title="E-Shop Analytics",
    page_icon="🛒",
    layout="wide"
)

# ==========================================
# CONEXÃO COM MONGODB
# ==========================================

@st.cache_resource
def conectar_mongodb():
    uri = os.getenv("MONGO_URI")

    for tentativa in range(15):
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000
            )
            client.admin.command("ping")
            return client
        except PyMongoError:
            time.sleep(2)

    return None


client = conectar_mongodb()

if client is None:
    st.error("Não foi possível conectar ao MongoDB.")
    st.stop()

db = client["eshop_brasil"]
clientes = db["clientes"]

# Índice para evitar e-mails duplicados
clientes.create_index(
    [("email", ASCENDING)],
    unique=True
)

# ==========================================
# CABEÇALHO
# ==========================================

st.title("🛒 E-Shop Analytics")
st.caption("Plataforma Inteligente de Gestão de Dados | E-Shop Brasil")

st.success("MongoDB conectado com sucesso!")

# ==========================================
# MENU LATERAL
# ==========================================

st.sidebar.title("Menu Principal")

pagina = st.sidebar.radio(
    "Selecione o módulo:",
    [
        "Dashboard",
        "Gerenciamento de Clientes",
        "Gerenciamento de Produtos",
        "Gerenciamento de Pedidos"
    ]
)

# ==========================================
# DASHBOARD
# ==========================================


# ==========================================
# DASHBOARD EXECUTIVO - BIG DATA
# ==========================================

if pagina == "Dashboard":

    st.header("📊 Dashboard Executivo")
    st.caption(
        "Inteligência de negócios | E-Shop Brasil"
    )

    clientes = db["clientes"]
    produtos = db["produtos"]
    pedidos = db["pedidos"]

    # --------------------------------------
    # COLETA DOS INDICADORES
    # --------------------------------------

    total_clientes = clientes.count_documents({})

    total_produtos = produtos.count_documents({})

    total_pedidos = pedidos.count_documents({})

    pedidos_validos = list(
        pedidos.find({"status": {"$ne": "Cancelado"}})
    )

    quantidade_vendas = len(pedidos_validos)

    faturamento = sum(
        float(p.get("valor_total", 0))
        for p in pedidos_validos
    )

    estoque_baixo = produtos.count_documents({
        "estoque": {"$lte": 5}
    })

    unidades_estoque = list(
        produtos.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$estoque"}
                }
            }
        ])
    )

    total_unidades = (
        unidades_estoque[0]["total"]
        if unidades_estoque else 0
    )

    # --------------------------------------
    # CARDS DE INDICADORES
    # --------------------------------------

    st.subheader("Indicadores gerais")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Faturamento válido",
        f"R$ {faturamento:,.2f}"
    )

    c2.metric(
        "Pedidos válidos",
        quantidade_vendas
    )

    c3.metric(
        "Clientes cadastrados",
        total_clientes
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Produtos cadastrados",
        total_produtos
    )

    c5.metric(
        "Unidades em estoque",
        total_unidades
    )

    c6.metric(
        "Produtos com estoque baixo",
        estoque_baixo,
        delta=(
            "Atenção necessária"
            if estoque_baixo > 0
            else "Estoque normal"
        ),
        delta_color="inverse"
    )

    st.divider()

    # --------------------------------------
    # EVOLUÇÃO DAS VENDAS
    # --------------------------------------

    st.subheader("📈 Evolução do faturamento")

    evolucao = list(
        pedidos.aggregate([
            {
                "$match": {
                    "status": {"$ne": "Cancelado"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "faturamento": {
                        "$sum": "$valor_total"
                    },
                    "pedidos": {
                        "$sum": 1
                    }
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ])
    )

    if evolucao:

        df_evolucao = pd.DataFrame([
            {
                "Data": item["_id"],
                "Faturamento": item["faturamento"],
                "Pedidos": item["pedidos"]
            }
            for item in evolucao
        ])

        fig = px.line(
            df_evolucao,
            x="Data",
            y="Faturamento",
            markers=True,
            title="Faturamento por dia",
            labels={
                "Data": "Data",
                "Faturamento": "Faturamento (R$)"
            }
        )

        fig.update_layout(
            template="plotly_dark",
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Registre pedidos para visualizar a evolução do faturamento."
        )

    st.divider()

    # --------------------------------------
    # PRODUTOS MAIS VENDIDOS
    # --------------------------------------

    st.subheader("🏆 Produtos mais vendidos")

    ranking = list(
        pedidos.aggregate([
            {
                "$match": {
                    "status": {"$ne": "Cancelado"}
                }
            },
            {
                "$group": {
                    "_id": "$produto_id",
                    "quantidade_vendida": {
                        "$sum": "$quantidade"
                    },
                    "faturamento": {
                        "$sum": "$valor_total"
                    }
                }
            },
            {
                "$lookup": {
                    "from": "produtos",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "produto"
                }
            },
            {
                "$unwind": "$produto"
            },
            {
                "$project": {
                    "nome": "$produto.nome",
                    "quantidade_vendida": 1,
                    "faturamento": 1
                }
            },
            {
                "$sort": {
                    "quantidade_vendida": -1
                }
            },
            {
                "$limit": 10
            }
        ])
    )

    if ranking:

        df_ranking = pd.DataFrame([
            {
                "Produto": item["nome"],
                "Quantidade vendida": item["quantidade_vendida"],
                "Faturamento": item["faturamento"]
            }
            for item in ranking
        ])

        fig_ranking = px.bar(
            df_ranking,
            x="Produto",
            y="Quantidade vendida",
            title="Top 10 produtos mais vendidos",
            text="Quantidade vendida"
        )

        fig_ranking.update_layout(
            template="plotly_dark"
        )

        st.plotly_chart(
            fig_ranking,
            use_container_width=True
        )

    else:

        st.info("Ainda não existem vendas para gerar o ranking.")

    st.divider()

    # --------------------------------------
    # VENDAS POR CATEGORIA
    # --------------------------------------

    st.subheader("📦 Desempenho por categoria")

    categorias = list(
        pedidos.aggregate([
            {
                "$match": {
                    "status": {"$ne": "Cancelado"}
                }
            },
            {
                "$lookup": {
                    "from": "produtos",
                    "localField": "produto_id",
                    "foreignField": "_id",
                    "as": "produto"
                }
            },
            {
                "$unwind": "$produto"
            },
            {
                "$group": {
                    "_id": "$produto.categoria",
                    "faturamento": {
                        "$sum": "$valor_total"
                    }
                }
            },
            {
                "$sort": {
                    "faturamento": -1
                }
            }
        ])
    )

    if categorias:

        df_categoria = pd.DataFrame([
            {
                "Categoria": item["_id"] or "Sem categoria",
                "Faturamento": item["faturamento"]
            }
            for item in categorias
        ])

        fig_categoria = px.pie(
            df_categoria,
            names="Categoria",
            values="Faturamento",
            title="Distribuição do faturamento por categoria",
            hole=0.4
        )

        fig_categoria.update_layout(
            template="plotly_dark"
        )

        st.plotly_chart(
            fig_categoria,
            use_container_width=True
        )

    else:

        st.info("Ainda não existem dados por categoria.")

    st.divider()

    # --------------------------------------
    # CONTROLE DE ESTOQUE
    # --------------------------------------

    st.subheader("🚨 Monitoramento de estoque")

    estoque_critico = list(
        produtos.find({
            "estoque": {"$lte": 5}
        }).sort("estoque", ASCENDING)
    )

    if estoque_critico:

        df_estoque = pd.DataFrame([
            {
                "Produto": item.get("nome", ""),
                "SKU": item.get("sku", ""),
                "Categoria": item.get("categoria", ""),
                "Quantidade": item.get("estoque", 0),
                "Situação": (
                    "Sem estoque"
                    if item.get("estoque", 0) == 0
                    else "Estoque baixo"
                )
            }
            for item in estoque_critico
        ])

        st.warning(
            f"{len(estoque_critico)} produto(s) precisam de atenção."
        )

        st.dataframe(
            df_estoque,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "Nenhum produto apresenta estoque crítico."
        )

    st.divider()

    # --------------------------------------
    # RESUMO EXECUTIVO
    # --------------------------------------

    st.subheader("💡 Resumo estratégico")

    if faturamento > 0:

        st.write(
            f"A E-Shop Brasil registrou "
            f"R$ {faturamento:,.2f} em faturamento "
            f"válido, distribuído em "
            f"{quantidade_vendas} pedidos."
        )

    else:

        st.write(
            "Aguardando registros de vendas para gerar "
            "indicadores de desempenho."
        )

    st.write(
        f"A base possui {total_clientes} clientes, "
        f"{total_produtos} produtos e "
        f"{total_unidades} unidades disponíveis em estoque."
    )

    st.caption(
        "E-Shop Analytics | Dashboard de Business Intelligence"
    )

# ==========================================
# GERENCIAMENTO DE CLIENTES
# ==========================================

elif pagina == "Gerenciamento de Clientes":

    st.header("👥 Gerenciamento de Clientes")

    st.write(
        "Cadastre, consulte, edite e exclua clientes "
        "diretamente no banco de dados MongoDB."
    )

    total = clientes.count_documents({})

    st.metric("Total de clientes cadastrados", total)

    aba1, aba2, aba3, aba4 = st.tabs(
        [
            "Cadastrar",
            "Consultar",
            "Editar",
            "Excluir"
        ]
    )

    # ======================================
    # CADASTRAR CLIENTE
    # ======================================

    with aba1:

        st.subheader("Novo cadastro")

        with st.form("form_cadastro_cliente"):

            nome = st.text_input("Nome completo")

            email = st.text_input("E-mail")

            telefone = st.text_input("Telefone")

            cidade = st.text_input("Cidade")

            estado = st.text_input("Estado (UF)", max_chars=2)

            enviar = st.form_submit_button(
                "Cadastrar cliente",
                use_container_width=True
            )

            if enviar:

                if not nome.strip() or not email.strip():
                    st.error("Nome e e-mail são obrigatórios.")

                elif "@" not in email or "." not in email:
                    st.error("Informe um e-mail válido.")

                elif len(estado.strip()) not in (0, 2):
                    st.error("Informe uma UF com duas letras.")

                else:

                    documento = {
                        "nome": nome.strip(),
                        "email": email.strip().lower(),
                        "telefone": telefone.strip(),
                        "cidade": cidade.strip(),
                        "estado": estado.strip().upper()
                    }

                    try:
                        clientes.insert_one(documento)

                        st.success(
                            f"Cliente {nome} cadastrado com sucesso!"
                        )

                    except DuplicateKeyError:
                        st.error(
                            "Este e-mail já está cadastrado."
                        )

                    except PyMongoError as erro:
                        st.error(f"Erro ao cadastrar: {erro}")

    # ======================================
    # CONSULTAR CLIENTES
    # ======================================

    with aba2:

        st.subheader("Clientes cadastrados")

        pesquisa = st.text_input(
            "Pesquisar por nome, e-mail ou cidade"
        )

        filtro = {}

        if pesquisa.strip():

            filtro = {
                "$or": [
                    {"nome": {"$regex": pesquisa, "$options": "i"}},
                    {"email": {"$regex": pesquisa, "$options": "i"}},
                    {"cidade": {"$regex": pesquisa, "$options": "i"}}
                ]
            }

        registros = list(
            clientes.find(filtro).sort("nome", ASCENDING)
        )

        if registros:

            dados = [
                {
                    "ID": str(item["_id"]),
                    "Nome": item.get("nome", ""),
                    "E-mail": item.get("email", ""),
                    "Telefone": item.get("telefone", ""),
                    "Cidade": item.get("cidade", ""),
                    "Estado": item.get("estado", "")
                }
                for item in registros
            ]

            df = pd.DataFrame(dados)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Total de registros encontrados: {len(registros)}"
            )

        else:
            st.info("Nenhum cliente encontrado.")

    # ======================================
    # EDITAR CLIENTE
    # ======================================

    with aba3:

        st.subheader("Editar cadastro")

        lista_clientes = list(
            clientes.find().sort("nome", ASCENDING)
        )

        if lista_clientes:

            opcoes = {
                f"{item.get('nome', '')} - {item.get('email', '')}":
                item
                for item in lista_clientes
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                list(opcoes.keys())
            )

            registro = opcoes[selecionado]

            with st.form("form_editar_cliente"):

                novo_nome = st.text_input(
                    "Nome",
                    value=registro.get("nome", "")
                )

                novo_email = st.text_input(
                    "E-mail",
                    value=registro.get("email", "")
                )

                novo_telefone = st.text_input(
                    "Telefone",
                    value=registro.get("telefone", "")
                )

                nova_cidade = st.text_input(
                    "Cidade",
                    value=registro.get("cidade", "")
                )

                novo_estado = st.text_input(
                    "Estado (UF)",
                    value=registro.get("estado", ""),
                    max_chars=2
                )

                salvar = st.form_submit_button(
                    "Salvar alterações",
                    use_container_width=True
                )

                if salvar:

                    if not novo_nome.strip() or not novo_email.strip():
                        st.error("Nome e e-mail são obrigatórios.")

                    elif "@" not in novo_email or "." not in novo_email:
                        st.error("Informe um e-mail válido.")

                    elif len(novo_estado.strip()) not in (0, 2):
                        st.error("Informe uma UF com duas letras.")

                    else:

                        atualizacao = {
                            "nome": novo_nome.strip(),
                            "email": novo_email.strip().lower(),
                            "telefone": novo_telefone.strip(),
                            "cidade": nova_cidade.strip(),
                            "estado": novo_estado.strip().upper()
                        }

                        try:

                            clientes.update_one(
                                {"_id": registro["_id"]},
                                {"$set": atualizacao}
                            )

                            st.success(
                                "Cadastro atualizado com sucesso!"
                            )

                        except DuplicateKeyError:
                            st.error(
                                "Este e-mail pertence a outro cliente."
                            )

                        except PyMongoError as erro:
                            st.error(f"Erro ao atualizar: {erro}")

        else:
            st.info("Não existem clientes para editar.")

    # ======================================
    # EXCLUIR CLIENTE
    # ======================================

    with aba4:

        st.subheader("Excluir cadastro")

        lista_exclusao = list(
            clientes.find().sort("nome", ASCENDING)
        )

        if lista_exclusao:

            opcoes_exclusao = {
                f"{item.get('nome', '')} - {item.get('email', '')}":
                item
                for item in lista_exclusao
            }

            escolhido = st.selectbox(
                "Selecione o cliente para exclusão",
                list(opcoes_exclusao.keys()),
                key="cliente_exclusao"
            )

            registro_exclusao = opcoes_exclusao[escolhido]

            st.warning(
                f"Você está prestes a excluir: "
                f"{registro_exclusao.get('nome', '')}"
            )

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este cadastro."
            )

            if st.button(
                "Excluir cliente",
                type="primary",
                disabled=not confirmar
            ):

                try:

                    clientes.delete_one(
                        {"_id": registro_exclusao["_id"]}
                    )

                    st.success("Cliente excluído com sucesso!")

                except PyMongoError as erro:
                    st.error(f"Erro ao excluir: {erro}")

        else:
            st.info("Não existem clientes cadastrados para excluir.")

# ==========================================
# GERENCIAMENTO DE PRODUTOS
# ==========================================

elif pagina == "Gerenciamento de Produtos":

    st.header("📦 Gerenciamento de Produtos")

    st.write(
        "Controle o catálogo, os preços e a disponibilidade "
        "dos produtos da E-Shop Brasil."
    )

    produtos = db["produtos"]

    # Evitar SKU duplicado
    produtos.create_index(
        [("sku", ASCENDING)],
        unique=True
    )

    total_produtos = produtos.count_documents({})

    estoque_baixo = produtos.count_documents({
        "estoque": {"$lte": 5}
    })

    col1, col2, col3 = st.columns(3)

    col1.metric("Produtos cadastrados", total_produtos)
    col2.metric("Estoque baixo", estoque_baixo)
    col3.metric("Banco de dados", "MongoDB")

    st.divider()

    aba1, aba2, aba3, aba4 = st.tabs([
        "Cadastrar",
        "Consultar",
        "Editar",
        "Excluir"
    ])

    # ======================================
    # CADASTRAR PRODUTO
    # ======================================

    with aba1:

        st.subheader("Cadastrar novo produto")

        with st.form("form_cadastro_produto"):

            nome = st.text_input("Nome do produto")

            sku = st.text_input("Código SKU")

            categoria = st.selectbox(
                "Categoria",
                [
                    "Eletrônicos",
                    "Informática",
                    "Moda",
                    "Casa e Decoração",
                    "Eletrodomésticos",
                    "Esportes",
                    "Outros"
                ]
            )

            preco = st.number_input(
                "Preço (R$)",
                min_value=0.01,
                value=99.90,
                step=10.0
            )

            estoque = st.number_input(
                "Quantidade em estoque",
                min_value=0,
                value=10,
                step=1
            )

            descricao = st.text_area(
                "Descrição do produto"
            )

            cadastrar = st.form_submit_button(
                "Cadastrar produto",
                use_container_width=True
            )

            if cadastrar:

                if not nome.strip() or not sku.strip():
                    st.error("Nome e SKU são obrigatórios.")

                else:

                    documento = {
                        "nome": nome.strip(),
                        "sku": sku.strip().upper(),
                        "categoria": categoria,
                        "preco": float(preco),
                        "estoque": int(estoque),
                        "descricao": descricao.strip()
                    }

                    try:

                        produtos.insert_one(documento)

                        st.success(
                            f"Produto {nome} cadastrado com sucesso!"
                        )

                    except DuplicateKeyError:
                        st.error("Este SKU já está cadastrado.")

                    except PyMongoError as erro:
                        st.error(f"Erro ao cadastrar: {erro}")

    # ======================================
    # CONSULTAR PRODUTOS
    # ======================================

    with aba2:

        st.subheader("Catálogo de produtos")

        pesquisa = st.text_input(
            "Pesquisar produto por nome ou SKU"
        )

        categoria_filtro = st.selectbox(
            "Filtrar por categoria",
            [
                "Todas",
                "Eletrônicos",
                "Informática",
                "Moda",
                "Casa e Decoração",
                "Eletrodomésticos",
                "Esportes",
                "Outros"
            ]
        )

        filtro = {}

        if pesquisa.strip():
            filtro["$or"] = [
                {
                    "nome": {
                        "$regex": pesquisa,
                        "$options": "i"
                    }
                },
                {
                    "sku": {
                        "$regex": pesquisa,
                        "$options": "i"
                    }
                }
            ]

        if categoria_filtro != "Todas":
            filtro["categoria"] = categoria_filtro

        registros = list(
            produtos.find(filtro).sort("nome", ASCENDING)
        )

        if registros:

            dados = [
                {
                    "SKU": item.get("sku", ""),
                    "Produto": item.get("nome", ""),
                    "Categoria": item.get("categoria", ""),
                    "Preço (R$)": item.get("preco", 0),
                    "Estoque": item.get("estoque", 0),
                    "Situação": (
                        "Estoque baixo"
                        if item.get("estoque", 0) <= 5
                        else "Disponível"
                    )
                }
                for item in registros
            ]

            df = pd.DataFrame(dados)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Produtos encontrados: {len(registros)}"
            )

            st.download_button(
                "📥 Exportar produtos em CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name="catalogo_eshop.csv",
                mime="text/csv"
            )

        else:
            st.info("Nenhum produto encontrado.")

    # ======================================
    # EDITAR PRODUTO
    # ======================================

    with aba3:

        st.subheader("Editar produto")

        lista = list(
            produtos.find().sort("nome", ASCENDING)
        )

        if lista:

            opcoes = {
                f"{item.get('nome', '')} - {item.get('sku', '')}":
                item
                for item in lista
            }

            selecionado = st.selectbox(
                "Selecione o produto",
                list(opcoes.keys())
            )

            registro = opcoes[selecionado]

            categorias = [
                "Eletrônicos",
                "Informática",
                "Moda",
                "Casa e Decoração",
                "Eletrodomésticos",
                "Esportes",
                "Outros"
            ]

            categoria_atual = registro.get(
                "categoria", "Outros"
            )

            if categoria_atual not in categorias:
                categorias.append(categoria_atual)

            with st.form("form_editar_produto"):

                novo_nome = st.text_input(
                    "Nome",
                    value=registro.get("nome", "")
                )

                novo_sku = st.text_input(
                    "SKU",
                    value=registro.get("sku", "")
                )

                nova_categoria = st.selectbox(
                    "Categoria",
                    categorias,
                    index=categorias.index(categoria_atual)
                )

                novo_preco = st.number_input(
                    "Preço (R$)",
                    min_value=0.01,
                    value=max(
                        0.01,
                        float(registro.get("preco", 0.01))
                    ),
                    step=10.0
                )

                novo_estoque = st.number_input(
                    "Estoque",
                    min_value=0,
                    value=max(
                        0,
                        int(registro.get("estoque", 0))
                    ),
                    step=1
                )

                nova_descricao = st.text_area(
                    "Descrição",
                    value=registro.get("descricao", "")
                )

                salvar = st.form_submit_button(
                    "Salvar alterações",
                    use_container_width=True
                )

                if salvar:

                    if not novo_nome.strip() or not novo_sku.strip():
                        st.error("Nome e SKU são obrigatórios.")

                    else:

                        atualizacao = {
                            "nome": novo_nome.strip(),
                            "sku": novo_sku.strip().upper(),
                            "categoria": nova_categoria,
                            "preco": float(novo_preco),
                            "estoque": int(novo_estoque),
                            "descricao": nova_descricao.strip()
                        }

                        try:

                            produtos.update_one(
                                {"_id": registro["_id"]},
                                {"$set": atualizacao}
                            )

                            st.success(
                                "Produto atualizado com sucesso!"
                            )

                        except DuplicateKeyError:
                            st.error("Este SKU já pertence a outro produto.")

                        except PyMongoError as erro:
                            st.error(f"Erro ao atualizar: {erro}")

        else:
            st.info("Não existem produtos cadastrados.")

    # ======================================
    # EXCLUIR PRODUTO
    # ======================================

    with aba4:

        st.subheader("Excluir produto")

        lista_exclusao = list(
            produtos.find().sort("nome", ASCENDING)
        )

        if lista_exclusao:

            opcoes_exclusao = {
                f"{item.get('nome', '')} - {item.get('sku', '')}":
                item
                for item in lista_exclusao
            }

            escolhido = st.selectbox(
                "Selecione o produto",
                list(opcoes_exclusao.keys()),
                key="produto_exclusao"
            )

            registro_exclusao = opcoes_exclusao[escolhido]

            st.warning(
                f"Produto selecionado: "
                f"{registro_exclusao.get('nome', '')}"
            )

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este produto."
            )

            if st.button(
                "Excluir produto",
                type="primary",
                disabled=not confirmar
            ):

                try:

                    produtos.delete_one({
                        "_id": registro_exclusao["_id"]
                    })

                    st.success("Produto excluído com sucesso!")

                except PyMongoError as erro:
                    st.error(f"Erro ao excluir: {erro}")

        else:
            st.info("Não existem produtos para excluir.")

# ==========================================
# GERENCIAMENTO DE PEDIDOS
# ==========================================

elif pagina == "Gerenciamento de Pedidos":

    st.header("🛍️ Gerenciamento de Pedidos")

    st.write(
        "Registre vendas, relacione clientes e produtos "
        "e acompanhe os pedidos da E-Shop Brasil."
    )

    pedidos = db["pedidos"]
    clientes = db["clientes"]
    produtos = db["produtos"]

    pedidos.create_index(
        [("created_at", -1)]
    )

    # Indicadores
    total_pedidos = pedidos.count_documents({})
    pedidos_ativos = pedidos.count_documents({
        "status": "Em processamento"
    })
    pedidos_cancelados = pedidos.count_documents({
        "status": "Cancelado"
    })

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de pedidos", total_pedidos)
    col2.metric("Em processamento", pedidos_ativos)
    col3.metric("Cancelados", pedidos_cancelados)

    st.divider()

    aba1, aba2, aba3 = st.tabs([
        "Novo pedido",
        "Consultar pedidos",
        "Cancelar pedido"
    ])

    # ======================================
    # NOVO PEDIDO
    # ======================================

    with aba1:

        st.subheader("Registrar novo pedido")

        lista_clientes = list(
            clientes.find().sort("nome", ASCENDING)
        )

        lista_produtos = list(
            produtos.find({
                "estoque": {"$gt": 0}
            }).sort("nome", ASCENDING)
        )

        if not lista_clientes:
            st.warning(
                "Cadastre pelo menos um cliente antes de registrar pedidos."
            )

        elif not lista_produtos:
            st.warning(
                "Não existem produtos disponíveis em estoque."
            )

        else:

            opcoes_clientes = {
                f"{c['nome']} - {c['email']}": c
                for c in lista_clientes
            }

            opcoes_produtos = {
                f"{p['nome']} - {p['sku']} (R$ {p['preco']:.2f})": p
                for p in lista_produtos
            }

            with st.form("form_novo_pedido"):

                cliente_escolhido = st.selectbox(
                    "Selecione o cliente",
                    list(opcoes_clientes.keys())
                )

                produto_escolhido = st.selectbox(
                    "Selecione o produto",
                    list(opcoes_produtos.keys())
                )

                produto_selecionado = opcoes_produtos[
                    produto_escolhido
                ]

                quantidade = st.number_input(
                    "Quantidade",
                    min_value=1,
                    max_value=max(
                        1,
                        int(produto_selecionado["estoque"])
                    ),
                    value=1,
                    step=1
                )

                total = (
                    float(produto_selecionado["preco"])
                    * int(quantidade)
                )

                st.info(
                    f"Preço unitário: "
                    f"R$ {produto_selecionado['preco']:.2f}"
                )

                st.metric(
                    "Valor total do pedido",
                    f"R$ {total:,.2f}"
                )

                registrar = st.form_submit_button(
                    "Registrar pedido",
                    use_container_width=True
                )

                if registrar:

                    cliente_selecionado = opcoes_clientes[
                        cliente_escolhido
                    ]

                    # Baixa segura do estoque
                    resultado = produtos.update_one(
                        {
                            "_id": produto_selecionado["_id"],
                            "estoque": {"$gte": int(quantidade)}
                        },
                        {
                            "$inc": {
                                "estoque": -int(quantidade)
                            }
                        }
                    )

                    if resultado.modified_count == 0:

                        st.error(
                            "Estoque insuficiente. "
                            "Atualize a página e tente novamente."
                        )

                    else:

                        documento = {
                            "cliente_id": cliente_selecionado["_id"],
                            "produto_id": produto_selecionado["_id"],
                            "quantidade": int(quantidade),
                            "preco_unitario": float(
                                produto_selecionado["preco"]
                            ),
                            "valor_total": round(total, 2),
                            "status": "Em processamento",
                            "created_at": datetime.utcnow()
                        }

                        try:

                            pedidos.insert_one(documento)

                            st.success(
                                "Pedido registrado com sucesso!"
                            )

                            st.balloons()

                        except PyMongoError as erro:

                            # Devolver estoque se o pedido falhar
                            produtos.update_one(
                                {"_id": produto_selecionado["_id"]},
                                {
                                    "$inc": {
                                        "estoque": int(quantidade)
                                    }
                                }
                            )

                            st.error(
                                f"Erro ao registrar pedido: {erro}"
                            )

    # ======================================
    # CONSULTAR PEDIDOS
    # ======================================

    with aba2:

        st.subheader("Histórico de pedidos")

        # Concatenação entre coleções usando $lookup
        registros = list(
            pedidos.aggregate([
                {
                    "$lookup": {
                        "from": "clientes",
                        "localField": "cliente_id",
                        "foreignField": "_id",
                        "as": "cliente"
                    }
                },
                {
                    "$lookup": {
                        "from": "produtos",
                        "localField": "produto_id",
                        "foreignField": "_id",
                        "as": "produto"
                    }
                },
                {
                    "$unwind": {
                        "path": "$cliente",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$unwind": {
                        "path": "$produto",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$sort": {
                        "created_at": -1
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "cliente": "$cliente.nome",
                        "email": "$cliente.email",
                        "produto": "$produto.nome",
                        "sku": "$produto.sku",
                        "quantidade": 1,
                        "preco_unitario": 1,
                        "valor_total": 1,
                        "status": 1,
                        "created_at": 1
                    }
                }
            ])
        )

        if registros:

            dados = []

            for pedido in registros:

                data = pedido.get("created_at")

                dados.append({
                    "Pedido": str(pedido["_id"])[-8:].upper(),
                    "Cliente": pedido.get(
                        "cliente", "Cliente não localizado"
                    ),
                    "E-mail": pedido.get("email", ""),
                    "Produto": pedido.get(
                        "produto", "Produto não localizado"
                    ),
                    "SKU": pedido.get("sku", ""),
                    "Quantidade": pedido.get("quantidade", 0),
                    "Preço unitário (R$)": pedido.get(
                        "preco_unitario", 0
                    ),
                    "Total (R$)": pedido.get("valor_total", 0),
                    "Status": pedido.get("status", ""),
                    "Data": (
                        data.strftime("%d/%m/%Y %H:%M")
                        if data else ""
                    )
                })

            df = pd.DataFrame(dados)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "📥 Exportar pedidos em CSV",
                data=df.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name="pedidos_eshop.csv",
                mime="text/csv"
            )

        else:

            st.info(
                "Nenhum pedido registrado até o momento."
            )

    # ======================================
    # CANCELAR PEDIDO
    # ======================================

    with aba3:

        st.subheader("Cancelar pedido")

        lista_pedidos = list(
            pedidos.find({
                "status": "Em processamento"
            }).sort("created_at", -1)
        )

        if lista_pedidos:

            opcoes_pedidos = {
                (
                    f"Pedido {str(p['_id'])[-8:].upper()} - "
                    f"R$ {p['valor_total']:.2f}"
                ): p
                for p in lista_pedidos
            }

            escolhido = st.selectbox(
                "Selecione o pedido",
                list(opcoes_pedidos.keys())
            )

            pedido_selecionado = opcoes_pedidos[escolhido]

            st.warning(
                "O cancelamento devolverá os produtos "
                "ao estoque, desde que ainda existam "
                "as referências do produto."
            )

            confirmar = st.checkbox(
                "Confirmo o cancelamento deste pedido."
            )

            if st.button(
                "Cancelar pedido",
                type="primary",
                disabled=not confirmar
            ):

                try:

                    resultado = pedidos.update_one(
                        {
                            "_id": pedido_selecionado["_id"],
                            "status": "Em processamento"
                        },
                        {
                            "$set": {
                                "status": "Cancelado",
                                "cancelled_at": datetime.utcnow()
                            }
                        }
                    )

                    if resultado.modified_count:

                        # Reposição do estoque
                        produtos.update_one(
                            {
                                "_id": pedido_selecionado["produto_id"]
                            },
                            {
                                "$inc": {
                                    "estoque": pedido_selecionado[
                                        "quantidade"
                                    ]
                                }
                            }
                        )

                        st.success(
                            "Pedido cancelado e estoque atualizado!"
                        )

                    else:

                        st.warning(
                            "O pedido já foi alterado ou cancelado."
                        )

                except PyMongoError as erro:

                    st.error(
                        f"Erro ao cancelar pedido: {erro}"
                    )

        else:

            st.info(
                "Não existem pedidos disponíveis para cancelamento."
            )
# ==========================================
# RODAPÉ
# ==========================================

st.divider()

st.caption(
    "E-Shop Analytics | Projeto acadêmico | "
    "MongoDB + Python + Streamlit"
)
