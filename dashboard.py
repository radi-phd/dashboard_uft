# ============================================================
# PAINEL ANALÍTICO INSTITUCIONAL
# Universidade Federal do Tocantins
# ============================================================

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Painel Analítico · UFT",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PALETA CORPORATIVA
# ============================================================

COR_PRIMARIA   = "#0D2B4E"
COR_SECUNDARIA = "#1A4A7A"
COR_ACENTO     = "#1E6FBF"
COR_DESTAQUE   = "#C8A84B"
COR_FUNDO      = "#F4F6F9"
COR_CARD       = "#FFFFFF"
COR_BORDA      = "#DDE3EC"
COR_TEXTO      = "#0D2B4E"
COR_TEXTO_LEVE = "#6B7A99"
COR_ALERTA     = "#E07B00"
COR_SUCESSO    = "#1B7A4A"

SEQUENCIA_AZUL = [
    "#C8D8EE",
    "#93B5D8",
    "#5E92C2",
    "#2F6FAC",
    "#0D4C8B",
    "#0A3366"
]

# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown(f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    color: {COR_TEXTO};
}}

.main {{
    background-color: {COR_FUNDO};
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        {COR_PRIMARIA} 0%,
        {COR_SECUNDARIA} 100%
    );
}}

[data-testid="stSidebar"] * {{
    color: white !important;
}}

.kpi-card {{
    background: white;
    border: 1px solid {COR_BORDA};
    border-radius: 14px;
    padding: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    text-align: center;
}}

.kpi-valor {{
    font-size: 2rem;
    font-weight: 700;
    color: {COR_PRIMARIA};
}}

.kpi-label {{
    font-size: 0.8rem;
    color: {COR_TEXTO_LEVE};
    text-transform: uppercase;
}}

.chart-card {{
    background: white;
    border: 1px solid {COR_BORDA};
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

.header {{
    background: linear-gradient(
        135deg,
        {COR_PRIMARIA} 0%,
        {COR_SECUNDARIA} 100%
    );
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    color: white;
}}

.header h1 {{
    margin: 0;
    font-family: 'Lora', serif;
}}

.header p {{
    opacity: 0.8;
}}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LEITURA DA PLANILHA
# ============================================================

ARQUIVO = "perfil.xlsx"

if not os.path.exists(ARQUIVO):

    st.error(f"""
Arquivo não encontrado:

{ARQUIVO}

Verifique:
- se o arquivo está na mesma pasta do dashboard.py
- se o nome está correto
- se o Excel está fechado
""")

    st.stop()

# ============================================================
# LEITURA DAS ABAS
# ============================================================

abas = pd.read_excel(
    ARQUIVO,
    sheet_name=None,
    engine="openpyxl"
)

nomes_abas = list(abas.keys())

aba_tecnico = None
aba_docente = None

for aba in nomes_abas:

    nome = (
        aba.lower()
        .replace("é", "e")
        .replace("ê", "e")
        .replace("á", "a")
        .replace("ã", "a")
        .replace("ç", "c")
        .strip()
    )

    if "tecnico" in nome:
        aba_tecnico = aba

    if "docente" in nome:
        aba_docente = aba

if aba_tecnico is None or aba_docente is None:

    st.error(f"""
As abas de técnico e docente não foram encontradas.

Abas disponíveis:
{nomes_abas}
""")

    st.stop()

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

df = df.loc[:, ~df.columns.duplicated()]

# ============================================================
# REMOVE DADOS SENSÍVEIS
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
# DATAS
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
        tit.str.contains(r"\bDOUT", na=False),
        "TITULACAO_CLASSIFICADA"
    ] = "DOUTORADO"

    df.loc[
        (
            tit.str.contains(r"\bMEST", na=False)
        )
        &
        (
            ~tit.str.contains(r"\bDOUT", na=False)
        ),
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
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ FILTROS")

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

# ============================================================
# FILTROS
# ============================================================

df_f = df.copy()

df_f = df_f[
    df_f["CATEGORIA"]
    .isin(categoria_sel)
]

if "SEXO" in df_f.columns:

    df_f = df_f[
        df_f["SEXO"]
        .isin(sexo_sel)
    ]

if "TITULACAO_CLASSIFICADA" in df_f.columns:

    df_f = df_f[
        df_f["TITULACAO_CLASSIFICADA"]
        .isin(titulacao_sel)
    ]

# ============================================================
# DESVIO
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df_f.columns
    and
    "LOTAÇÃO_EXERCÍCIO" in df_f.columns
):

    df_f["DESVIO"] = np.where(
        df_f["LOTAÇÃO_OFICIAL"]
        !=
        df_f["LOTAÇÃO_EXERCÍCIO"],
        "SIM",
        "NÃO"
    )

# ============================================================
# KPIs
# ============================================================

total = len(df_f)

docentes = len(
    df_f[df_f["CATEGORIA"] == "DOCENTE"]
)

tecnicos = len(
    df_f[df_f["CATEGORIA"] == "TÉCNICO"]
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
# ÍNDICE MÉDIO
# ============================================================

pesos = {
    "DOUTORADO": 4,
    "MESTRADO": 3,
    "ESPECIALIZAÇÃO": 2,
    "GRADUAÇÃO": 1
}

score = 0

for nivel, peso in pesos.items():

    qtd = len(
        df_f[
            df_f["TITULACAO_CLASSIFICADA"]
            == nivel
        ]
    )

    score += qtd * peso

indice_medio = round(
    score / max(total, 1),
    2
)

# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(f"""
<div class="header">
    <h1>🎓 Painel Analítico Institucional</h1>
    <p>
        Universidade Federal do Tocantins ·
        Gestão Estratégica de Pessoas
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{total}</div>
        <div class="kpi-label">Total</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{docentes}</div>
        <div class="kpi-label">Docentes</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{tecnicos}</div>
        <div class="kpi-label">Técnicos</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{doutores}</div>
        <div class="kpi-label">Doutores</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{mestres}</div>
        <div class="kpi-label">Mestres</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-valor">{indice_medio}</div>
        <div class="kpi-label">Qualificação</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# GRÁFICOS
# ============================================================

g1, g2 = st.columns(2)

# ============================================================
# TITULAÇÃO
# ============================================================

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

        fig_tit = px.bar(
            tit,
            x="Quantidade",
            y="Titulação",
            orientation="h",
            text_auto=True,
            color="Quantidade",
            color_continuous_scale=SEQUENCIA_AZUL,
            height=450
        )

        fig_tit.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            coloraxis_showscale=False,
            font=dict(
                family="DM Sans"
            )
        )

        st.markdown(
            '<div class="chart-card">',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            fig_tit,
            width="stretch"
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

# ============================================================
# SEXO
# ============================================================

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

        fig_sexo = px.pie(
            sexo,
            names="Sexo",
            values="Quantidade",
            hole=0.6,
            height=450,
            color_discrete_sequence=[
                COR_PRIMARIA,
                COR_DESTAQUE,
                COR_ACENTO
            ]
        )

        fig_sexo.update_layout(
            paper_bgcolor="white",
            font=dict(
                family="DM Sans"
            )
        )

        st.markdown(
            '<div class="chart-card">',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            fig_sexo,
            width="stretch"
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

# ============================================================
# LOTAÇÃO
# ============================================================

if "LOTAÇÃO_OFICIAL" in df_f.columns:

    st.subheader("🏢 Lotação Oficial")

    lot = (
        df_f["LOTAÇÃO_OFICIAL"]
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
        color="Quantidade",
        color_continuous_scale=SEQUENCIA_AZUL,
        height=650
    )

    fig_lot.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        coloraxis_showscale=False,
        font=dict(
            family="DM Sans"
        )
    )

    st.markdown(
        '<div class="chart-card">',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        fig_lot,
        width="stretch"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# ============================================================
# HEATMAP
# ============================================================

if (
    "LOTAÇÃO_OFICIAL" in df_f.columns
    and
    "CATEGORIA" in df_f.columns
):

    st.subheader("🔥 Heatmap Institucional")

    heat = pd.crosstab(
        df_f["LOTAÇÃO_OFICIAL"],
        df_f["CATEGORIA"]
    )

    fig_heat = px.imshow(
        heat,
        text_auto=True,
        aspect="auto",
        height=700,
        color_continuous_scale="Blues"
    )

    fig_heat.update_layout(
        paper_bgcolor="white",
        font=dict(
            family="DM Sans"
        )
    )

    st.markdown(
        '<div class="chart-card">',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        fig_heat,
        width="stretch"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# ============================================================
# IDADE
# ============================================================

if "IDADE" in df_f.columns:

    st.subheader("📈 Distribuição Etária")

    fig_idade = px.histogram(
        df_f,
        x="IDADE",
        nbins=20,
        height=450,
        color_discrete_sequence=[COR_ACENTO]
    )

    fig_idade.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="DM Sans"
        )
    )

    st.markdown(
        '<div class="chart-card">',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        fig_idade,
        width="stretch"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# ============================================================
# TABELA
# ============================================================

st.subheader("📄 Base Consolidada")

st.dataframe(
    df_f,
    width="stretch",
    height=450
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