# ============================================================
# PAINEL ANALÍTICO INSTITUCIONAL
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="PAINEL ANALÍTICO INSTITUCIONAL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #F8FAFC;
}

h1, h2, h3 {
    color: #0F172A;
}

[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #E2E8F0;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 1px 3px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LEITURA DA PLANILHA
# ============================================================

ARQUIVO = "perfil.xlsx"

abas = pd.read_excel(
    ARQUIVO,
    sheet_name=None
)

# ============================================================
# LEITURA DAS ABAS
# ============================================================

tecnico = abas["técnico"].copy()
docente = abas["docente"].copy()

tecnico["CATEGORIA"] = "TÉCNICO"
docente["CATEGORIA"] = "DOCENTE"

# ============================================================
# CONSOLIDAÇÃO
# ============================================================

df = pd.concat(
    [tecnico, docente],
    ignore_index=True
)

# ============================================================
# REMOVE COLUNAS DUPLICADAS
# ============================================================

df = df.loc[
    :,
    ~df.columns.duplicated()
]

# ============================================================
# REMOVE DADOS SENSÍVEIS (LGPD)
# ============================================================

colunas_sensiveis = [
    "CPF",
    "CPF_SERVIDOR",
    "RG",
    "DOCUMENTO",
    "NOME"
]

df = df.drop(
    columns=[
        col for col in colunas_sensiveis
        if col in df.columns
    ],
    errors="ignore"
)

# ============================================================
# PADRONIZAÇÃO
# ============================================================

for col in df.columns:

    if df[col].dtype == "object":

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

# ============================================================
# TRATAMENTO DE DATAS
# ============================================================

if "DT_NASC" in df.columns:

    df["DT_NASC"] = pd.to_datetime(
        df["DT_NASC"],
        errors="coerce",
        dayfirst=True
    )

    hoje = pd.Timestamp.today()

    df["IDADE"] = (
        (hoje - df["DT_NASC"])
        .dt.days / 365.25
    ).round(1)

# ============================================================
# REMOVE ÍNDICES DUPLICADOS
# ============================================================

df = df.reset_index(drop=True)

# ============================================================
# CLASSIFICAÇÃO DE TITULAÇÃO
# ============================================================

if "TITULAÇÃO" in df.columns:

    tit = (
        df["TITULAÇÃO"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["TITULACAO_CLASSIFICADA"] = "OUTROS"

    # DOUTORADO
    df.loc[
        tit.str.contains(
            r"\bDOUT",
            regex=True,
            na=False
        ),
        "TITULACAO_CLASSIFICADA"
    ] = "DOUTORADO"

    # MESTRADO
    df.loc[
        (
            tit.str.contains(
                r"\bMEST",
                regex=True,
                na=False
            )
        )
        &
        (
            ~tit.str.contains(
                r"\bDOUT",
                regex=True,
                na=False
            )
        ),
        "TITULACAO_CLASSIFICADA"
    ] = "MESTRADO"

    # ESPECIALIZAÇÃO
    df.loc[
        tit.str.contains(
            "ESPECIAL",
            na=False
        ),
        "TITULACAO_CLASSIFICADA"
    ] = "ESPECIALIZAÇÃO"

    # GRADUAÇÃO
    df.loc[
        tit.str.contains(
            "GRAD",
            na=False
        ),
        "TITULACAO_CLASSIFICADA"
    ] = "GRADUAÇÃO"

    # ENSINO MÉDIO / TÉCNICO
    df.loc[
        tit.str.contains(
            "2 GRAU|TECNICO",
            na=False
        ),
        "TITULACAO_CLASSIFICADA"
    ] = "ENSINO MÉDIO/TÉCNICO"

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ FILTROS DINÂMICOS")

# ------------------------------------------------------------
# CATEGORIA
# ------------------------------------------------------------

categorias = sorted(
    df["CATEGORIA"]
    .dropna()
    .unique()
)

categoria_sel = st.sidebar.multiselect(
    "Categoria",
    categorias,
    default=categorias
)

# ------------------------------------------------------------
# SEXO
# ------------------------------------------------------------

if "SEXO" in df.columns:

    sexos = sorted(
        df["SEXO"]
        .dropna()
        .unique()
    )

    sexo_sel = st.sidebar.multiselect(
        "Sexo",
        sexos,
        default=sexos
    )

else:
    sexo_sel = []

# ------------------------------------------------------------
# TITULAÇÃO
# ------------------------------------------------------------

if "TITULACAO_CLASSIFICADA" in df.columns:

    titulacoes = sorted(
        df["TITULACAO_CLASSIFICADA"]
        .dropna()
        .unique()
    )

    titulacao_sel = st.sidebar.multiselect(
        "Titulação",
        titulacoes,
        default=titulacoes
    )

else:
    titulacao_sel = []

# ------------------------------------------------------------
# LOTAÇÃO
# ------------------------------------------------------------

if "LOTAÇÃO_OFICIAL" in df.columns:

    lotacoes = sorted(
        df["LOTAÇÃO_OFICIAL"]
        .dropna()
        .unique()
    )

    lotacao_sel = st.sidebar.multiselect(
        "Lotação Oficial",
        lotacoes,
        default=lotacoes
    )

else:
    lotacao_sel = []

# ============================================================
# FILTROS
# ============================================================

df_filtrado = df.copy()

df_filtrado = df_filtrado[
    df_filtrado["CATEGORIA"]
    .isin(categoria_sel)
]

if "SEXO" in df_filtrado.columns:

    df_filtrado = df_filtrado[
        df_filtrado["SEXO"]
        .isin(sexo_sel)
    ]

if "TITULACAO_CLASSIFICADA" in df_filtrado.columns:

    df_filtrado = df_filtrado[
        df_filtrado["TITULACAO_CLASSIFICADA"]
        .isin(titulacao_sel)
    ]

if "LOTAÇÃO_OFICIAL" in df_filtrado.columns:

    df_filtrado = df_filtrado[
        df_filtrado["LOTAÇÃO_OFICIAL"]
        .isin(lotacao_sel)
    ]

# ============================================================
# RESETA ÍNDICES
# ============================================================

df_filtrado = df_filtrado.reset_index(drop=True)

# ============================================================
# DESVIO DE LOTAÇÃO
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df_filtrado.columns
    and
    "LOTAÇÃO_EXERCÍCIO" in df_filtrado.columns
):

    df_filtrado["DESVIO"] = np.where(
        df_filtrado["LOTAÇÃO_OFICIAL"]
        !=
        df_filtrado["LOTAÇÃO_EXERCÍCIO"],
        "SIM",
        "NÃO"
    )

# ============================================================
# CABEÇALHO
# ============================================================

st.markdown("""
# 📊 Painel Analítico Institucional

### Universidade Federal do Tocantins

Distribuição funcional, qualificação acadêmica
e análise estratégica da força de trabalho.
""")

# ============================================================
# KPIs
# ============================================================

total = len(df_filtrado)

docentes = len(
    df_filtrado[
        df_filtrado["CATEGORIA"] == "DOCENTE"
    ]
)

tecnicos = len(
    df_filtrado[
        df_filtrado["CATEGORIA"] == "TÉCNICO"
    ]
)

# ============================================================
# DOUTORES
# ============================================================

doutores = 0

if "TITULACAO_CLASSIFICADA" in df_filtrado.columns:

    doutores = len(
        df_filtrado[
            df_filtrado["TITULACAO_CLASSIFICADA"]
            == "DOUTORADO"
        ]
    )

# ============================================================
# MESTRES
# ============================================================

mestres = 0

if "TITULACAO_CLASSIFICADA" in df_filtrado.columns:

    mestres = len(
        df_filtrado[
            df_filtrado["TITULACAO_CLASSIFICADA"]
            == "MESTRADO"
        ]
    )

# ============================================================
# ÍNDICE DE QUALIFICAÇÃO
# ============================================================

score = 0

if "TITULACAO_CLASSIFICADA" in df_filtrado.columns:

    pesos = {
        "DOUTORADO": 4,
        "MESTRADO": 3,
        "ESPECIALIZAÇÃO": 2,
        "GRADUAÇÃO": 1,
        "ENSINO MÉDIO/TÉCNICO": 0
    }

    for nivel, peso in pesos.items():

        qtd = len(
            df_filtrado[
                df_filtrado["TITULACAO_CLASSIFICADA"]
                == nivel
            ]
        )

        score += qtd * peso

# ============================================================
# QUALIFICAÇÃO MÉDIA
# ============================================================

indice_medio = round(
    score / max(total, 1),
    2
)

# ============================================================
# CLASSIFICAÇÃO DO NÍVEL
# ============================================================

if indice_medio >= 3.5:
    nivel_qualificacao = "MUITO ALTA"

elif indice_medio >= 3:
    nivel_qualificacao = "ALTA"

elif indice_medio >= 2:
    nivel_qualificacao = "MODERADA"

else:
    nivel_qualificacao = "BAIXA"

# ============================================================
# PERCENTUAL DE DESVIO
# ============================================================

if "DESVIO" in df_filtrado.columns:

    percentual_desvio = round(
        (
            len(
                df_filtrado[
                    df_filtrado["DESVIO"] == "SIM"
                ]
            )
            / max(len(df_filtrado), 1)
        ) * 100,
        2
    )

else:
    percentual_desvio = 0

# ============================================================
# KPIs VISUAIS
# ============================================================

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Total", total)
k2.metric("Docentes", docentes)
k3.metric("Técnicos", tecnicos)
k4.metric("Doutores", doutores)
k5.metric("Mestres", mestres)

k6.metric(
    "Qualificação Média",
    f"{indice_medio} / 4.0"
)

# ============================================================
# INTERPRETAÇÃO EXECUTIVA
# ============================================================

st.info(f"""
📘 Nível de Qualificação Institucional: {nivel_qualificacao}

Escala de interpretação:
- 0 → Sem qualificação
- 1 → Graduação
- 2 → Especialização
- 3 → Mestrado
- 4 → Doutorado
""")

# ============================================================
# ALERTA EXECUTIVO
# ============================================================

st.warning(f"""
⚠️ Aproximadamente {percentual_desvio}% dos registros apresentam divergência entre lotação oficial e exercício funcional.
""")

# ============================================================
# GAUGE DE QUALIFICAÇÃO
# ============================================================

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=indice_medio,
    title={'text': "Qualificação Média Institucional"},
    gauge={
        'axis': {'range': [0, 4]}
    }
))

st.plotly_chart(
    fig_gauge,
    width="stretch"
)

# ============================================================
# LINHA 1
# ============================================================

g1, g2 = st.columns(2)

# ------------------------------------------------------------
# TITULAÇÃO
# ------------------------------------------------------------

with g1:

    if "TITULACAO_CLASSIFICADA" in df_filtrado.columns:

        st.subheader("🎓 Distribuição por Titulação")

        tit = (
            df_filtrado["TITULACAO_CLASSIFICADA"]
            .value_counts()
            .reset_index()
        )

        tit.columns = [
            "Titulação",
            "Quantidade"
        ]

        fig_tit = px.bar(
            tit,
            x="Quantidade",
            y="Titulação",
            orientation="h",
            text_auto=True,
            height=500
        )

        st.plotly_chart(
            fig_tit,
            width="stretch"
        )

# ------------------------------------------------------------
# SEXO
# ------------------------------------------------------------

with g2:

    if "SEXO" in df_filtrado.columns:

        st.subheader("👥 Distribuição por Sexo")

        sexo = (
            df_filtrado["SEXO"]
            .value_counts()
            .reset_index()
        )

        sexo.columns = [
            "Sexo",
            "Quantidade"
        ]

        fig_sexo = px.pie(
            sexo,
            names="Sexo",
            values="Quantidade",
            hole=0.5,
            height=500
        )

        st.plotly_chart(
            fig_sexo,
            width="stretch"
        )

# ============================================================
# LINHA 2
# ============================================================

g3, g4 = st.columns(2)

# ------------------------------------------------------------
# LOTAÇÃO
# ------------------------------------------------------------

with g3:

    if "LOTAÇÃO_OFICIAL" in df_filtrado.columns:

        st.subheader("🏢 Concentração por Lotação")

        lot = (
            df_filtrado["LOTAÇÃO_OFICIAL"]
            .value_counts()
            .head(15)
            .reset_index()
        )

        lot.columns = [
            "Lotação",
            "Quantidade"
        ]

        fig_lot = px.bar(
            lot,
            x="Quantidade",
            y="Lotação",
            orientation="h",
            text_auto=True,
            height=600
        )

        st.plotly_chart(
            fig_lot,
            width="stretch"
        )

# ------------------------------------------------------------
# CARGOS
# ------------------------------------------------------------

with g4:

    if "CARGO" in df_filtrado.columns:

        st.subheader("📌 Distribuição por Cargo")

        cargos = (
            df_filtrado["CARGO"]
            .value_counts()
            .head(15)
            .reset_index()
        )

        cargos.columns = [
            "Cargo",
            "Quantidade"
        ]

        fig_cargo = px.bar(
            cargos,
            x="Quantidade",
            y="Cargo",
            orientation="h",
            text_auto=True,
            height=600
        )

        st.plotly_chart(
            fig_cargo,
            width="stretch"
        )

# ============================================================
# HEATMAP
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df_filtrado.columns
    and
    "CATEGORIA" in df_filtrado.columns
):

    st.subheader("🔥 Heatmap Institucional")

    heat = pd.crosstab(
        df_filtrado["LOTAÇÃO_OFICIAL"],
        df_filtrado["CATEGORIA"]
    )

    fig_heat = px.imshow(
        heat,
        text_auto=True,
        aspect="auto",
        height=700
    )

    st.plotly_chart(
        fig_heat,
        width="stretch"
    )

# ============================================================
# DESVIO DE LOTAÇÃO
# ============================================================

if "DESVIO" in df_filtrado.columns:

    st.subheader("⚠️ Desvio de Lotação")

    desvio = (
        df_filtrado["DESVIO"]
        .value_counts()
        .reset_index()
    )

    desvio.columns = [
        "Desvio",
        "Quantidade"
    ]

    fig_desvio = px.pie(
        desvio,
        names="Desvio",
        values="Quantidade",
        hole=0.6,
        height=500
    )

    st.plotly_chart(
        fig_desvio,
        width="stretch"
    )

# ============================================================
# ANÁLISE ETÁRIA
# ============================================================

if "IDADE" in df_filtrado.columns:

    st.subheader("📈 Distribuição Etária")

    fig_idade = px.histogram(
        df_filtrado,
        x="IDADE",
        nbins=20,
        height=500
    )

    st.plotly_chart(
        fig_idade,
        width="stretch"
    )

# ============================================================
# RANKING INSTITUCIONAL
# ============================================================

if "LOTAÇÃO_OFICIAL" in df_filtrado.columns:

    st.subheader("🏆 Ranking Institucional")

    ranking = (
        df_filtrado["LOTAÇÃO_OFICIAL"]
        .value_counts()
        .reset_index()
    )

    ranking.columns = [
        "Campus / Unidade",
        "Quantidade"
    ]

    st.dataframe(
        ranking,
        width="stretch",
        height=400
    )

# ============================================================
# BASE FILTRADA
# ============================================================

st.subheader("📄 Base Consolidada Filtrada")

st.dataframe(
    df_filtrado,
    width="stretch",
    height=500
)

# ============================================================
# DOWNLOAD CSV
# ============================================================

csv = df_filtrado.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Baixar Base Filtrada",
    data=csv,
    file_name="base_filtrada.csv",
    mime="text/csv"
)