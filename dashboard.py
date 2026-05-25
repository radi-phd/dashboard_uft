# ============================================================
# PAINEL ANALÍTICO INSTITUCIONAL
# Universidade Federal do Tocantins
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Painel Analítico NAEGD - UFT",
    page_icon="🎓",
    layout="wide"
)

# ============================================================
# CORES
# ============================================================

COR_PRIMARIA = "#0D2B4E"
COR_SECUNDARIA = "#1A4A7A"
COR_FUNDO = "#F4F6F9"
COR_CARD = "#FFFFFF"
COR_BORDA = "#DDE3EC"
COR_ALERTA = "#E07B00"
COR_SUCESSO = "#1B7A4A"

# ============================================================
# CSS
# ============================================================

st.markdown(f"""
<style>

.main {{
    background-color: {COR_FUNDO};
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        {COR_PRIMARIA},
        {COR_SECUNDARIA}
    );
}}

[data-testid="stSidebar"] * {{
    color: white !important;
}}

.kpi {{
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid {COR_BORDA};
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}

.kpi h2 {{
    margin: 0;
    color: {COR_PRIMARIA};
}}

.kpi p {{
    margin: 0;
    color: #666;
    font-size: 13px;
}}

.header {{
    background: linear-gradient(
        135deg,
        {COR_PRIMARIA},
        {COR_SECUNDARIA}
    );

    padding: 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 25px;
}}

.chart {{
    background: white;
    padding: 15px;
    border-radius: 14px;
    border: 1px solid {COR_BORDA};
    margin-bottom: 20px;
}}

</style>
""", unsafe_allow_html=True)

# ============================================================
# IDENTIFICAÇÃO AUTOMÁTICA DO ARQUIVO
# ============================================================

arquivo = None

for arq in os.listdir():

    if arq.endswith(".xlsx") or arq.endswith(".xls"):

        arquivo = arq
        break

if arquivo is None:

    st.error(
        "Nenhum arquivo Excel encontrado na pasta."
    )

    st.stop()

# ============================================================
# LEITURA DO EXCEL
# ============================================================

try:

    abas = pd.read_excel(
        arquivo,
        sheet_name=None
    )

except Exception as e:

    st.error(f"Erro ao abrir o Excel: {e}")
    st.stop()

# ============================================================
# IDENTIFICAÇÃO DAS ABAS
# ============================================================

nomes_abas = list(abas.keys())

aba_tecnico = None
aba_docente = None

for nome in nomes_abas:

    nome_tratado = (
        str(nome)
        .strip()
        .lower()
        .replace("é", "e")
        .replace("ê", "e")
        .replace("á", "a")
        .replace("ã", "a")
        .replace("ç", "c")
    )

    if "tec" in nome_tratado:
        aba_tecnico = nome

    if "doc" in nome_tratado:
        aba_docente = nome

# ============================================================
# VALIDAÇÃO
# ============================================================

if aba_tecnico is None or aba_docente is None:

    st.error("Abas técnico/docente não encontradas.")

    st.write("Abas disponíveis:")
    st.write(nomes_abas)

    st.stop()

# ============================================================
# LEITURA DAS ABAS
# ============================================================

tecnico = abas[aba_tecnico].copy()
docente = abas[aba_docente].copy()

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
# REMOVE DADOS SENSÍVEIS
# ============================================================

colunas_sensiveis = [
    "CPF",
    "RG",
    "DOCUMENTO",
    "NOME"
]

df = df.drop(
    columns=[
        c for c in colunas_sensiveis
        if c in df.columns
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
# DATA / IDADE
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
# TITULAÇÃO
# ============================================================

if "TITULAÇÃO" in df.columns:

    tit = (
        df["TITULAÇÃO"]
        .astype(str)
        .str.upper()
    )

    df["TITULACAO_CLASSIFICADA"] = "OUTROS"

    df.loc[
        tit.str.contains("DOUT", na=False),
        "TITULACAO_CLASSIFICADA"
    ] = "DOUTORADO"

    df.loc[
        tit.str.contains("MEST", na=False),
        "TITULACAO_CLASSIFICADA"
    ] = "MESTRADO"

    df.loc[
        tit.str.contains("ESPECIAL", na=False),
        "TITULACAO_CLASSIFICADA"
    ] = "ESPECIALIZAÇÃO"

    df.loc[
        tit.str.contains("GRAD", na=False),
        "TITULACAO_CLASSIFICADA"
    ] = "GRADUAÇÃO"

# ============================================================
# DESVIO
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df.columns
    and
    "LOTAÇÃO_EXERCÍCIO" in df.columns
):

    df["DESVIO"] = np.where(
        df["LOTAÇÃO_OFICIAL"]
        !=
        df["LOTAÇÃO_EXERCÍCIO"],
        "SIM",
        "NÃO"
    )

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ FILTROS")

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
        "Lotação",
        lotacoes,
        default=lotacoes
    )

else:
    lotacao_sel = []

# ------------------------------------------------------------
# CARGO
# ------------------------------------------------------------

if "CARGO" in df.columns:

    cargos = sorted(
        df["CARGO"]
        .dropna()
        .unique()
    )

    cargo_sel = st.sidebar.multiselect(
        "Cargo",
        cargos,
        default=cargos
    )

else:
    cargo_sel = []

# ============================================================
# FILTROS
# ============================================================

df_f = df.copy()

df_f = df_f[
    df_f["CATEGORIA"]
    .isin(categoria_sel)
]

if "TITULACAO_CLASSIFICADA" in df_f.columns:

    df_f = df_f[
        df_f["TITULACAO_CLASSIFICADA"]
        .isin(titulacao_sel)
    ]

if "LOTAÇÃO_OFICIAL" in df_f.columns:

    df_f = df_f[
        df_f["LOTAÇÃO_OFICIAL"]
        .isin(lotacao_sel)
    ]

if "CARGO" in df_f.columns:

    df_f = df_f[
        df_f["CARGO"]
        .isin(cargo_sel)
    ]

# ============================================================
# KPIs
# ============================================================

total = len(df_f)

docentes = len(
    df_f[
        df_f["CATEGORIA"] == "DOCENTE"
    ]
)

tecnicos = len(
    df_f[
        df_f["CATEGORIA"] == "TÉCNICO"
    ]
)

doutores = 0
mestres = 0

if "TITULACAO_CLASSIFICADA" in df_f.columns:

    doutores = len(
        df_f[
            df_f["TITULACAO_CLASSIFICADA"]
            == "DOUTORADO"
        ]
    )

    mestres = len(
        df_f[
            df_f["TITULACAO_CLASSIFICADA"]
            == "MESTRADO"
        ]
    )

# ============================================================
# SCORE
# ============================================================

score = 0

pesos = {
    "DOUTORADO": 4,
    "MESTRADO": 3,
    "ESPECIALIZAÇÃO": 2,
    "GRADUAÇÃO": 1
}

if "TITULACAO_CLASSIFICADA" in df_f.columns:

    for nivel, peso in pesos.items():

        qtd = len(
            df_f[
                df_f["TITULACAO_CLASSIFICADA"]
                == nivel
            ]
        )

        score += qtd * peso

indice = round(
    score / max(total, 1),
    2
)

# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(f"""
<div class="header">

<h1>🎓 Painel Analítico Institucional</h1>

Universidade Federal do Tocantins

</div>
""", unsafe_allow_html=True)

# ============================================================
# KPIs
# ============================================================

k1, k2, k3, k4, k5, k6 = st.columns(6)

def card(coluna, valor, titulo):

    with coluna:

        st.markdown(
            f"""
            <div class="kpi">
            <h2>{valor}</h2>
            <p>{titulo}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

card(k1, total, "TOTAL")
card(k2, docentes, "DOCENTES")
card(k3, tecnicos, "TÉCNICOS")
card(k4, doutores, "DOUTORES")
card(k5, mestres, "MESTRES")
card(k6, indice, "SCORE")

# ============================================================
# GAUGE
# ============================================================

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=indice,
    title={"text": "Qualificação Média"},
    gauge={
        "axis": {"range": [0, 4]},
        "bar": {"color": COR_PRIMARIA},
        "steps": [
            {"range": [0, 1], "color": "#DDEAF5"},
            {"range": [1, 2], "color": "#AAC7E6"},
            {"range": [2, 3], "color": "#5D96D0"},
            {"range": [3, 4], "color": "#0D4C8B"},
        ]
    }
))

st.markdown('<div class="chart">', unsafe_allow_html=True)

st.plotly_chart(
    fig_gauge,
    width="stretch"
)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# GRÁFICOS
# ============================================================

g1, g2 = st.columns(2)

# ------------------------------------------------------------
# TITULAÇÃO
# ------------------------------------------------------------

with g1:

    if "TITULACAO_CLASSIFICADA" in df_f.columns:

        tit = (
            df_f["TITULACAO_CLASSIFICADA"]
            .value_counts()
            .reset_index()
        )

        tit.columns = [
            "Titulação",
            "Quantidade"
        ]

        fig = px.bar(
            tit,
            x="Quantidade",
            y="Titulação",
            orientation="h",
            text_auto=True,
            color="Quantidade",
            color_continuous_scale="Blues",
            height=450
        )

        st.markdown('<div class="chart">', unsafe_allow_html=True)

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# SEXO
# ------------------------------------------------------------

with g2:

    if "SEXO" in df_f.columns:

        sexo = (
            df_f["SEXO"]
            .value_counts()
            .reset_index()
        )

        sexo.columns = [
            "Sexo",
            "Quantidade"
        ]

        fig = px.pie(
            sexo,
            names="Sexo",
            values="Quantidade",
            hole=0.6,
            height=450
        )

        st.markdown('<div class="chart">', unsafe_allow_html=True)

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CARGO
# ============================================================

if "CARGO" in df_f.columns:

    cargos = (
        df_f["CARGO"]
        .value_counts()
        .head(15)
        .reset_index()
    )

    cargos.columns = [
        "Cargo",
        "Quantidade"
    ]

    fig = px.bar(
        cargos,
        x="Quantidade",
        y="Cargo",
        orientation="h",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale="YlOrBr",
        height=600
    )

    st.markdown('<div class="chart">', unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# HEATMAP
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df_f.columns
    and
    "CATEGORIA" in df_f.columns
):

    heat = pd.crosstab(
        df_f["LOTAÇÃO_OFICIAL"],
        df_f["CATEGORIA"]
    )

    fig = px.imshow(
        heat,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        height=700
    )

    st.markdown('<div class="chart">', unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# IDADE
# ============================================================

if "IDADE" in df_f.columns:

    fig = px.histogram(
        df_f,
        x="IDADE",
        nbins=20,
        color_discrete_sequence=[COR_PRIMARIA],
        height=450
    )

    st.markdown('<div class="chart">', unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TABELA
# ============================================================

st.subheader("📄 Base Consolidada")

st.dataframe(
    df_f,
    width="stretch",
    height=500
)

# ============================================================
# DOWNLOAD
# ============================================================

csv = df_f.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Baixar CSV",
    data=csv,
    file_name="base_filtrada.csv",
    mime="text/csv"
)
