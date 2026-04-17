import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide", page_title="TurbAi - Análisis Político")

# Inyectar el CSS que ya tenías para mantener la estética
st.markdown("""
    <style>
    .ia-report-container {
        border-left: 5px solid #111827;
        background: #f9fafb;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data # Esto hace que la app sea veloz
def cargar_datos():
    # Asegúrate de que estos archivos estén en la misma carpeta que app.py
    df = pd.read_csv("tu_archivo_de_votos.csv") 
    muni = gpd.read_file("tu_mapa_municipios.geojson")
    return df, muni

try:
    df_agrupado, municipios = cargar_datos()
except:
    st.error("⚠️ No se encontraron los archivos de datos. Asegúrate de subirlos a GitHub.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
st.sidebar.title("🚀 TurbAi Dashboard")
st.sidebar.markdown("Desarrollado por **Caid Analitycs**")

dep_seleccionado = st.sidebar.selectbox("Seleccione Departamento:", ["NACIONAL"] + sorted(df_agrupado['DEPNOMBRE'].unique().tolist()))

# Filtro dinámico de municipios
if dep_seleccionado == 'NACIONAL':
    muni_opciones = ["Nivel Nacional"]
else:
    muni_opciones = ["TODOS"] + sorted(df_agrupado[df_agrupado['DEPNOMBRE'] == dep_seleccionado]['MUNNOMBRE'].unique().tolist())
muni_seleccionado = st.sidebar.selectbox("Seleccione Municipio:", muni_opciones)

# Otros filtros
corporacion = st.sidebar.selectbox("Corporación:", df_agrupado['CORNOMBRE'].unique())
partido = st.sidebar.selectbox("Partido:", df_agrupado[df_agrupado['CORNOMBRE'] == corporacion]['PARNOMBRE'].unique())

# --- LÓGICA DE FILTRADO ---
# (Aquí va la misma lógica de máscaras de pandas que ya tienes)
mask = (df_agrupado['CORNOMBRE'] == corporacion) & (df_agrupado['PARNOMBRE'] == partido)
if dep_seleccionado != "NACIONAL":
    mask &= (df_agrupado['DEPNOMBRE'] == dep_seleccionado)
    if muni_seleccionado != "TODOS":
        mask &= (df_agrupado['MUNNOMBRE'] == muni_seleccionado)

df_final = df_agrupado[mask].copy()

# --- VISUALIZACIÓN ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Votos", f"{df_final['VOTOS'].sum():,.0f}")
with col2:
    st.metric("Municipios", len(df_final['MUNNOMBRE'].unique()))

# --- EL MAPA ---
st.subheader("📍 Distribución Geográfica")
if not df_final.empty:
    # Agrupar para el mapa
    v_mapa = df_final.groupby('MUNNOMBRE').agg({'VOTOS': 'sum'}).reset_index()
    mapa_final = municipios.merge(v_mapa, on='MUNNOMBRE', how='left')
    
    m = mapa_final.explore(
        column="VOTOS",
        cmap="YlGnBu",
        tooltip=["MUNNOMBRE", "VOTOS"],
        style_kwds={"fillOpacity": 0.8}
    )
    
    # Mostrar mapa en Streamlit
    st_folium(m, width=1200, height=500)

# --- BOTÓN DE IA ---
if st.button("GENERAR ANÁLISIS TURB-AI"):
    with st.spinner("⚡ Procesando con Turb-AI..."):
        # Aquí llamarías a tu función generar_reporte_ia
        st.markdown('<div class="ia-report-container">Análisis generado con éxito...</div>', unsafe_allow_html=True)