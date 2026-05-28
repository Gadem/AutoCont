import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard CFDI", layout="wide")

st.title("📊 Dashboard de Facturas CFDI")

# Cargar datos
df = pd.read_excel("reporte.xlsx")

# Limpieza básica
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Total"] = pd.to_numeric(df["Total"], errors="coerce")

# Crear columna Mes
df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)

# ===== MÉTRICAS =====
col1, col2 = st.columns(2)

col1.metric("💰 Total Facturado", f"${df['Total'].sum():,.2f}")
col2.metric("🧾 Número de registros", len(df))

# ===== FILTROS =====
st.sidebar.header("Filtros")

rfc = st.sidebar.selectbox(
    "RFC Emisor",
    ["Todos"] + sorted(df["Emisor_RFC"].dropna().unique().tolist())
)

if rfc != "Todos":
    df = df[df["Emisor_RFC"] == rfc]

# ===== GRÁFICA =====
st.subheader("📅 Facturación por mes")

df_mes = df.groupby("Mes")["Total"].sum()

st.bar_chart(df_mes)

# ===== TABLA =====
st.subheader("📋 Detalle de facturas")

st.dataframe(df)