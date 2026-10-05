"""Dashboard - Produção de Energia no Brasil (Tema 6)
Disciplina: Linguagens de Programação
Professor: Alexandre Neves Louzada
Aluno: Dagner Costa Leal
"""
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sqlalchemy import create_engine

TITULO = "Produção de Energia no Brasil"
DISCIPLINA = "Linguagens de Programação"
PROFESSOR = "Alexandre Neves Louzada"
ALUNO = "Dagner Costa Leal"

BASE = Path(__file__).parent
CSV = BASE / "dados" / "simulacao_producao_energia_brasil.csv"
DB = BASE / "database" / "energia.db"

st.set_page_config(page_title=TITULO, page_icon="⚡", layout="wide")
sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------- utilidades
def norm(txt):
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return t.lower().strip()


def achar(df, *palavras, numerica=None):
    """Primeira coluna cujo nome contém alguma das palavras."""
    for c in df.columns:
        if numerica is True and not pd.api.types.is_numeric_dtype(df[c]):
            continue
        if any(p in norm(c) for p in palavras):
            return c
    return None


MESES = {m: i + 1 for i, m in enumerate(
    ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"])}


@st.cache_data(show_spinner="Carregando dados...")
def carregar(arquivo_bytes=None):
    origem = pd.io.common.BytesIO(arquivo_bytes) if arquivo_bytes else CSV
    df = pd.read_csv(origem, sep=",", encoding="utf-8-sig")
    # --- limpeza
    df.columns = [c.strip() for c in df.columns]
    df = df.drop_duplicates()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype(str).str.strip()
    # --- período
    c_data, c_ano, c_mes = achar(df, "data", "date"), achar(df, "ano"), achar(df, "mes")
    if c_data:
        df["periodo"] = pd.to_datetime(df[c_data], errors="coerce")
    elif c_ano:
        mes = 1
        if c_mes:
            m = pd.to_numeric(df[c_mes], errors="coerce")
            if m.isna().all():
                m = df[c_mes].map(lambda x: MESES.get(norm(x)[:3]))
            mes = m.fillna(1).astype(int)
        df["periodo"] = pd.to_datetime(dict(year=df[c_ano].astype(int), month=mes, day=1))
    df = df.dropna(subset=["periodo"]) if "periodo" in df else df
    if "periodo" in df:
        df["ano"] = df["periodo"].dt.year
        df["mes_num"] = df["periodo"].dt.month
    # --- nulos numéricos -> mediana
    for c in df.select_dtypes("number").columns:
        df[c] = df[c].fillna(df[c].median())
    return df


@st.cache_resource
def salvar_sqlite(df):
    """Persistência: grava a base tratada em SQLite via SQLAlchemy."""
    try:
        DB.parent.mkdir(exist_ok=True)
        eng = create_engine(f"sqlite:///{DB}")
        df.to_sql("producao_energia", eng, if_exists="replace", index=False)
        return eng
    except Exception:
        return create_engine("sqlite://")  # fallback em memória


def fmt(x):
    return f"{x:,.0f}".replace(",", ".") if abs(x) >= 100 else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- cabeçalho
st.title(f"⚡ {TITULO}")
st.caption(f"**Disciplina:** {DISCIPLINA}  |  **Professor:** {PROFESSOR}  |  **Aluno:** {ALUNO}")
st.markdown(
    "**Problema:** como a produção de energia se distribui pelo território brasileiro, "
    "entre fontes e ao longo do tempo? Este painel permite filtrar a base e identificar "
    "onde, quando e por quais fontes a produção se concentra. "
    "*(Base simulada, fornecida pelo professor.)*")

# ---------------------------------------------------------------- dados
st.sidebar.header("📂 Dados")
up = st.sidebar.file_uploader("Enviar outro CSV (opcional)", type="csv")
try:
    df = carregar(up.getvalue() if up else None)
except FileNotFoundError:
    st.error("Arquivo não encontrado. Coloque `simulacao_producao_energia_brasil.csv` na pasta `dados/`.")
    st.stop()
salvar_sqlite(df)

numericas = [c for c in df.select_dtypes("number").columns if c not in ("ano", "mes", "mes_num")]
cats = [c for c in df.select_dtypes(include=["object", "string"]).columns if 1 < df[c].nunique() <= 30]
padrao = achar(df, "produc", "geracao", "mwh", "energia", numerica=True) or numericas[0]

st.sidebar.header("🎛️ Filtros")
metrica = st.sidebar.selectbox("Métrica principal", numericas, index=numericas.index(padrao))
f = df.copy()
if "ano" in f:
    a0, a1 = int(f.ano.min()), int(f.ano.max())
    faixa = st.sidebar.slider("Período (anos)", a0, a1, (a0, a1)) if a0 < a1 else (a0, a1)
    f = f[f.ano.between(*faixa)]
for c in cats:
    escolha = st.sidebar.multiselect(c.replace("_", " ").title(), sorted(df[c].unique()), default=sorted(df[c].unique()))
    f = f[f[c].isin(escolha)]

if f.empty:
    st.warning("Nenhum registro com os filtros atuais. Amplie a seleção na barra lateral.")
    st.stop()

# ---------------------------------------------------------------- KPIs
anual = f.groupby("ano")[metrica].sum() if "ano" in f else None
var = None
if anual is not None and len(anual) > 1 and anual.iloc[0]:
    var = (anual.iloc[-1] / anual.iloc[0] - 1) * 100
k = st.columns(5)
k[0].metric("Total", fmt(f[metrica].sum()))
k[1].metric("Média por registro", fmt(f[metrica].mean()))
k[2].metric("Máximo", fmt(f[metrica].max()))
k[3].metric("Registros", f"{len(f):,}".replace(",", "."))
k[4].metric("Variação 1º→último ano", f"{var:+.1f}%" if var is not None else "—")

c_cons, c_co2 = achar(f, "consumo", numerica=True), achar(f, "co2", "emissao", numerica=True)
c_ren, c_custo = achar(f, "renov", numerica=True), achar(f, "custo", numerica=True)
k2 = st.columns(4)
if c_cons:
    saldo = f[metrica].sum() - f[c_cons].sum()
    k2[0].metric("Saldo (métrica − consumo)", fmt(saldo))
if c_co2:
    k2[1].metric("Emissão total de CO₂", fmt(f[c_co2].sum()))
if c_ren:
    k2[2].metric("% renovável (ponderado)", f"{np.average(f[c_ren], weights=f[metrica].clip(lower=0) + 1e-9):.1f}%")
if c_custo:
    k2[3].metric("Custo médio por MWh", fmt(f[c_custo].mean()))

abas = st.tabs(["📊 Visão geral", "📈 Temporal", "🔎 Comparações", "🔗 Correlação", "🗃️ Dados", "✅ Conclusão"])

# ---- Visão geral
with abas[0]:
    c1, c2 = st.columns(2)
    if cats:
        cat = c1.selectbox("Agrupar por", cats, key="g1")
        s = f.groupby(cat)[metrica].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x=s.values, y=s.index, ax=ax, color="#1d6fa5")
        ax.set(title=f"{metrica} total por {cat}", xlabel=metrica, ylabel="")
        c1.pyplot(fig)
        c2.dataframe(s.rename("total").to_frame().style.format("{:,.0f}"), use_container_width=True)
        st.info(f"**Interpretação:** **{s.index[0]}** lidera com {s.iloc[0] / s.sum():.1%} do total; "
                f"**{s.index[-1]}** tem a menor participação ({s.iloc[-1] / s.sum():.1%}).")
    fig, ax = plt.subplots(figsize=(10, 3))
    sns.histplot(f[metrica], bins=40, kde=True, ax=ax, color="#e6a117")
    ax.set(title=f"Distribuição de {metrica}")
    st.pyplot(fig)

# ---- Temporal
with abas[1]:
    if "periodo" in f:
        m = f.groupby("periodo")[metrica].sum()
        mm = m.rolling(12, min_periods=3).mean()
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(m.index, m.values, alpha=.4, label="Mensal")
        ax.plot(mm.index, mm.values, lw=2.5, color="#d1495b", label="Média móvel 12 meses")
        ax.set(title=f"Evolução de {metrica}"); ax.legend()
        st.pyplot(fig)
        if len(anual) > 1:
            yoy = anual.pct_change().mul(100).dropna()
            fig, ax = plt.subplots(figsize=(10, 3))
            sns.barplot(x=yoy.index, y=yoy.values, ax=ax, color="#1d6fa5")
            ax.axhline(0, color="k", lw=.8); ax.set(title="Variação anual (%)", xlabel="Ano", ylabel="%")
            st.pyplot(fig)
            st.info(f"**Interpretação:** maior alta em **{int(yoy.idxmax())}** ({yoy.max():+.1f}%) "
                    f"e maior queda/menor alta em **{int(yoy.idxmin())}** ({yoy.min():+.1f}%).")
    else:
        st.warning("A base não possui coluna de data/ano para análise temporal.")

# ---- Comparações
with abas[2]:
    if cats:
        cat = st.selectbox("Comparar por", cats, key="g2")
        ordem = f.groupby(cat)[metrica].median().sort_values(ascending=False).index
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(data=f, x=cat, y=metrica, hue=cat, order=ordem, ax=ax, palette="viridis", legend=False)
        plt.xticks(rotation=45, ha="right"); ax.set(title=f"{metrica} por {cat}")
        st.pyplot(fig)
        if "ano" in f:
            pv = f.pivot_table(index=cat, columns="ano", values=metrica, aggfunc="sum")
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.heatmap(pv, cmap="YlGnBu", ax=ax); ax.set(title=f"{metrica}: {cat} × ano")
            st.pyplot(fig)
        st.info(f"**Interpretação:** a maior mediana é de **{ordem[0]}**. Compare a dispersão (caixas) "
                "para ver quais grupos são mais estáveis.")

# ---- Correlação
with abas[3]:
    if len(numericas) > 1:
        corr = f[numericas].corr(method="pearson")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
        st.pyplot(fig)
        r = corr[metrica].drop(metrica).sort_values(key=abs, ascending=False)
        st.info(f"**Interpretação:** a variável mais associada a {metrica} é **{r.index[0]}** "
                f"(r = {r.iloc[0]:.2f}). Correlação não implica causalidade.")
    else:
        st.warning("São necessárias ao menos duas colunas numéricas.")

# ---- Dados
with abas[4]:
    st.dataframe(f.head(500), use_container_width=True)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", f.to_csv(index=False).encode(), "dados_filtrados.csv")
    st.caption("A base tratada também é gravada em `database/energia.db` (SQLite, via SQLAlchemy).")

# ---- Conclusão
with abas[5]:
    st.subheader("Conclusão executiva")
    txt = [f"- A métrica **{metrica}** soma **{fmt(f[metrica].sum())}** nos filtros atuais."]
    if cats:
        s = f.groupby(cats[0])[metrica].sum().sort_values(ascending=False)
        txt.append(f"- Em **{cats[0]}**, **{s.index[0]}** concentra {s.iloc[0] / s.sum():.1%} do total.")
    if var is not None:
        txt.append(f"- Entre o primeiro e o último ano, a métrica variou **{var:+.1f}%**.")
    if len(numericas) > 1:
        txt.append(f"- A maior correlação com a métrica é com **{r.index[0]}** (r = {r.iloc[0]:.2f}).")
    txt.append("- Os dados são simulados; os resultados ilustram a metodologia, não a realidade do setor.")
    st.markdown("\n".join(txt))

st.divider()
st.caption(f"{TITULO} · {DISCIPLINA} · Prof. {PROFESSOR} · Aluno: {ALUNO}")
