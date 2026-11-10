# E-Shop Analytics

Sistema de gerenciamento e análise de dados para uma loja virtual, desenvolvido como projeto acadêmico da Faculdade UNIFECAF.

## Objetivo

Desenvolver uma aplicação para gerenciar clientes, produtos e pedidos, utilizando banco de dados NoSQL e recursos de análise de dados para apoiar a tomada de decisões.

## Tecnologias utilizadas

- Python
- Streamlit
- MongoDB 7.0
- Docker e Docker Compose
- Pandas
- Plotly

## Funcionalidades

### Gerenciamento de clientes
- Cadastro de clientes.
- Consulta de registros.
- Edição de informações.
- Exclusão de clientes.

### Gerenciamento de produtos
- Cadastro e manutenção de produtos.
- Consulta por nome e SKU.
- Filtro por categoria.
- Controle de estoque.
- Identificação de produtos com estoque baixo.
- Exportação de dados em CSV.

### Gerenciamento de pedidos
- Criação de pedidos vinculados a clientes e produtos.
- Cálculo automático do valor total.
- Atualização automática do estoque.
- Consulta do histórico de pedidos.
- Cancelamento de pedidos e reposição do estoque.

### Dashboard e análise de dados
- Indicadores de faturamento.
- Quantidade de pedidos, clientes e produtos.
- Acompanhamento do estoque.
- Gráfico de faturamento por período.
- Ranking de produtos mais vendidos.
- Análise de faturamento por categoria.

## Como executar o projeto

### Pré-requisitos

- Docker Desktop instalado e em execução.
- Git instalado (para clonar o repositório).

### Executar localmente

1. Clone o repositório:

```bash
git clone URL_DO_REPOSITORIO
```

2. Entre na pasta do projeto:

```bash
cd EShopAnalytics
```

3. Configure o arquivo `.env` com as credenciais do MongoDB, seguindo o modelo disponibilizado no projeto.

4. Inicie os containers:

```bash
docker compose up -d --build
```

5. Acesse a aplicação pelo navegador:

```text
http://localhost:8501
```

### Encerrar a aplicação

```bash
docker compose down
```

## Estrutura do projeto

```text
EShopAnalytics/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

**Importante:** o arquivo `.env` contém credenciais e não deve ser publicado no GitHub.

## Banco de dados

O projeto utiliza MongoDB, com coleções para:

- `clientes`
- `produtos`
- `pedidos`

Os dados são armazenados em volume persistente do Docker.

## Considerações finais

O E-Shop Analytics demonstra a aplicação prática de conceitos de desenvolvimento em Python, banco de dados NoSQL, conteinerização com Docker e análise de dados. A solução permite organizar informações comerciais e transformar os dados da operação em indicadores úteis para a gestão de uma loja virtual.

**Projeto acadêmico — Gestão da Tecnologia da Informação | Faculdade UNIFECAF**