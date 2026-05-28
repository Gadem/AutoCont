from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard CFDI", layout="wide")

st.title("📊 Dashboard de Facturas CFDI")

st.sidebar.header("Fuente de datos")
uploaded = st.sidebar.file_uploader("Sube un reporte (.xlsx o .csv)", type=["xlsx", "csv"])

df = None
if uploaded is not None:
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
else:
    default_xlsx = Path("reporte.xlsx")
    default_csv = Path("reporte.csv")
    if default_xlsx.exists():
        df = pd.read_excel(default_xlsx)
    elif default_csv.exists():
        df = pd.read_csv(default_csv)
    else:
        st.info("No se encontró `reporte.xlsx`/`reporte.csv`. Sube un archivo desde la barra lateral.")
        st.stop()

# Limpieza básica
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Total"] = pd.to_numeric(df["Total"], errors="coerce")

# Crear columna Mes
df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)

# ===== MÉTRICAS =====
col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Facturado", f"${df['Total'].sum():,.2f}")
col2.metric("🧾 Número de registros", len(df))
col3.metric("📅 Rango de fechas", f"{df['Fecha'].min().date()} → {df['Fecha'].max().date()}" if df["Fecha"].notna().any() else "N/A")

# ===== FILTROS =====
st.sidebar.header("Filtros")

min_date = df["Fecha"].min()
max_date = df["Fecha"].max()
if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input("Rango de fechas", value=(min_date.date(), max_date.date()))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["Fecha"].dt.date >= start) & (df["Fecha"].dt.date <= end)]

rfc = st.sidebar.selectbox(
    "RFC Emisor",
    ["Todos"] + sorted(df["Emisor_RFC"].dropna().unique().tolist())
)

if rfc != "Todos":
    df = df[df["Emisor_RFC"] == rfc]

receptor = st.sidebar.selectbox(
    "RFC Receptor",
    ["Todos"] + sorted(df.get("Receptor_RFC", pd.Series(dtype=str)).dropna().unique().tolist())
)
if receptor != "Todos" and "Receptor_RFC" in df.columns:
    df = df[df["Receptor_RFC"] == receptor]

moneda = st.sidebar.selectbox(
    "Moneda",
    ["Todas"] + sorted(df.get("Moneda", pd.Series(dtype=str)).dropna().unique().tolist())
)
if moneda != "Todas" and "Moneda" in df.columns:
    df = df[df["Moneda"] == moneda]

# ===== GRÁFICA =====
st.subheader("📅 Facturación por mes")

df_mes = df.groupby("Mes")["Total"].sum()

st.bar_chart(df_mes)

# ===== TOPS =====
top_cols = st.columns(2)
with top_cols[0]:
    st.subheader("🏢 Top emisores (Total)")
    if "Emisor_RFC" in df.columns:
        st.dataframe(df.groupby("Emisor_RFC")["Total"].sum().sort_values(ascending=False).head(10))
with top_cols[1]:
    st.subheader("👤 Top receptores (Total)")
    if "Receptor_RFC" in df.columns:
        st.dataframe(df.groupby("Receptor_RFC")["Total"].sum().sort_values(ascending=False).head(10))

# ===== TABLA =====
st.subheader("📋 Detalle de facturas")

st.dataframe(df)
