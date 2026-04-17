import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(layout="wide", page_title="TurbAi - Dashboard Electoral")

# 2. REFERENCIA VISUAL Y ESTILOS
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #1f2937 !important;
    }
    .filter-card {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .card-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #111827; }
    .ranking-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .ranking-table td { padding: 4px 6px; border-bottom: 1px solid #f3f4f6; }
    
    .ia-report-container {
        border-left: 4px solid #111827;
        background: #ffffff;
        padding: 20px;
        margin-top: 15px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        border-left-width: 5px;
    }
    .ia-badge {
        font-size: 9px;
        color: #6b7280 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 10px;
        display: block;
    }
    .ia-text { font-size: 13px !important; line-height: 1.7 !important; color: #374151 !important; text-align: justify; }
    .ia-text b, .ia-text strong { color: #111827 !important; font-weight: 700; }
    .ia-text p { margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# 3. CARGA DE DATOS
@st.cache_data
def cargar_datos():
    # Asegúrate de que el archivo se llame así. Si subiste un CSV sin comprimir, cambia el nombre aquí.
    df = pd.read_csv("datos_votos.zip") 
    muni = gpd.read_file("mapa_municipios.geojson")
    
    muni.index = muni.index.astype(str)
    df['VOTOS'] = pd.to_numeric(df['VOTOS'], errors='coerce').fillna(0)
    return df, muni

try:
    df_agrupado, municipios = cargar_datos()
except Exception as e:
    st.error(f"⚠️ Error cargando datos: {e}")
    st.stop()

# 4. EXTRACCIÓN DE LISTAS BASE
lista_dep_base = sorted(df_agrupado['DEPNOMBRE'].astype(str).unique().tolist())
lista_depnombre = ['NACIONAL'] + lista_dep_base 
lista_cornombre = sorted(df_agrupado['CORNOMBRE'].astype(str).unique().tolist())
lista_temas = ['YlGnBu', 'YlGn', 'YlOrRd', 'Blues', 'Greens', 'Oranges', 'coolwarm','RdYlGn', 'Spectral', 'RdBu', 'crest', 'viridis', 'Paired', 'Set3']

# ENCABEZADO PRINCIPAL
st.markdown('<div style="background:#111827; padding:15px; border-radius:8px 8px 0 0;"><h2 style="color:white; margin:0; font-size:18px;">Dashboard Electoral TurbAi</h2></div>', unsafe_allow_html=True)

# 5. WIDGETS Y LÓGICA DE FILTRADO (Cascada)
col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown('<div class="filter-card"><p class="card-title"><i class="fa fa-map-marker-alt"></i> Filtros Geográficos</p>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    dropdown_dep = c1.selectbox('Alcance:', lista_depnombre, index=0)
    check_excluir_dep = c2.checkbox('Excluir Depto', value=False)
    
    if dropdown_dep == 'NACIONAL':
        opciones_muni = ['Nivel Nacional']
        disabled_muni = True
    else:
        opciones_muni = ['TODOS'] + sorted(df_agrupado[df_agrupado['DEPNOMBRE'] == dropdown_dep]['MUNNOMBRE'].astype(str).unique().tolist())
        disabled_muni = False
        
    c3, c4 = st.columns([3, 1])
    dropdown_muni = c3.selectbox('Municipio:', opciones_muni, disabled=disabled_muni)
    check_excluir_muni = c4.checkbox('Excluir Muni', value=False, disabled=disabled_muni)
    st.markdown('</div>', unsafe_allow_html=True)

with col_der:
    st.markdown('<div class="filter-card"><p class="card-title"><i class="fa fa-users"></i> Selección de Candidatura</p>', unsafe_allow_html=True)
    dropdown_cor = st.selectbox('Corporación:', lista_cornombre)
    
    lista_parnombre = sorted(df_agrupado[df_agrupado['CORNOMBRE'] == dropdown_cor]['PARNOMBRE'].astype(str).unique().tolist())
    dropdown_par = st.selectbox('Partido:', lista_parnombre if lista_parnombre else ['Sin Partidos'])
    
    lista_can = sorted(df_agrupado[(df_agrupado['CORNOMBRE'] == dropdown_cor) & (df_agrupado['PARNOMBRE'] == dropdown_par)]['CANNOMBRE'].astype(str).unique().tolist())
    dropdown_can = st.selectbox('Candidato:', ['TODOS'] + lista_can if lista_can else ['Sin Candidatos'])
    
    dropdown_tema = st.selectbox('Paleta de colores:', lista_temas, index=0)
    st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÓN DE ACTUALIZAR ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 ACTUALIZAR VISUALIZACIÓN", type="primary", use_container_width=True):
    st.session_state['mostrar_reporte'] = True

# Solo procesar si el botón fue presionado alguna vez
if st.session_state.get('mostrar_reporte', False):
    with st.spinner("Procesando datos y generando mapas..."):
        
        # 6. FILTRADO DE DATOS FINAL
        mask_geo = pd.Series(True, index=df_agrupado.index)
        if dropdown_dep != 'NACIONAL':
            if check_excluir_dep: mask_geo &= (df_agrupado['DEPNOMBRE'] != dropdown_dep)
            else:
                mask_geo &= (df_agrupado['DEPNOMBRE'] == dropdown_dep)
                if dropdown_muni != 'TODOS':
                    if check_excluir_muni: mask_geo &= (df_agrupado['MUNNOMBRE'] != dropdown_muni)
                    else: mask_geo &= (df_agrupado['MUNNOMBRE'] == dropdown_muni)

        df_corp_geo = df_agrupado[(df_agrupado['CORNOMBRE'] == dropdown_cor) & mask_geo].copy()
        df_partido_geo = df_corp_geo[df_corp_geo['PARNOMBRE'] == dropdown_par].copy()

        query_final = (df_agrupado['CORNOMBRE'] == dropdown_cor) & (df_agrupado['PARNOMBRE'] == dropdown_par) & mask_geo
        if dropdown_can not in ['TODOS', 'Sin Candidatos']:
            query_final &= (df_agrupado['CANNOMBRE'] == dropdown_can)

        votos_final = df_agrupado[query_final].copy()

        # 7. PROCESAMIENTO DE LAS TABLAS
        if not votos_final.empty:
            top_muni = votos_final.groupby('MUNNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
            top_depto = votos_final.groupby('DEPNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
            top_partidos = df_corp_geo.groupby('PARNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
            
            if 'CANCEDULA' in df_partido_geo.columns:
                top_cand_partido = df_partido_geo[df_partido_geo['CANCEDULA'] > 0].groupby('CANNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
                top_cand_regional = df_corp_geo[df_corp_geo['CANCEDULA'] > 0].groupby('CANNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
            else:
                top_cand_partido = df_partido_geo.groupby('CANNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)
                top_cand_regional = df_corp_geo.groupby('CANNOMBRE')['VOTOS'].sum().sort_values(ascending=False).head(10)

            vm = votos_final.groupby(level=0)['VOTOS'].sum()

            stats_data = {
                'TOTAL VOTOS': vm.sum(),
                'PROMEDIO': vm.mean(),
                'MEDIANA': vm.median(),
                'MÁXIMO': vm.max(), 
                'DESVIACIÓN': vm.std(),
            }

            rangos_data = {
                'MUNICIPIOS': len(vm),
                '0 - 500 VOTOS': len(vm[vm <= 500]),
                '500 - 5k VOTOS': len(vm[(vm > 500) & (vm <= 5000)]),
                '5k - 20k VOTOS': len(vm[(vm > 5000) & (vm <= 20000)]),
                '> 20k VOTOS': len(vm[vm > 20000])
            }

            # FUNCIONES DE RENDERIZADO HTML
            def crear_col(titulo, serie, icono):
                html = f'<div style="flex: 1; padding: 0 8px; border-right: 1px solid #e5e7eb;">'
                html += f'<p class="card-title" style="text-align:center;"><i class="fa {icono}"></i> {titulo}</p><table class="ranking-table">'
                for idx, val in serie.items():
                    html += f'<tr><td style="font-size:10px;">{str(idx)[:15]}</td><td style="text-align:right; font-weight:600;">{val:,.0f}</td></tr>'
                return html + '</table></div>'

            def render_tabla_stats(titulo, diccionario, icono):
                html = f'<div style="flex: 1; padding: 0 8px;">'
                html += f'<p class="card-title" style="text-align:center;"><i class="fa {icono}"></i> {titulo}</p><table class="ranking-table">'
                for k, v in diccionario.items():
                    html += f'<tr><td style="font-size:10px;">{k}</td><td style="text-align:right; font-weight:600;">{v:,.0f}</td></tr>'
                return html + '</table></div>'

            # RENDERIZAR EL RECUADRO DE MÉTRICAS
            html_metricas = f"""
            <div class="filter-card" style="display: flex; flex-direction: row; justify-content: space-between; background-color: white; padding: 20px 10px;">
                {crear_col('TOP MUNICIPIOS', top_muni, 'fa-building')}
                {crear_col('TOP DEPTOS', top_depto, 'fa-map')}
                {crear_col('CAND. PARTIDO', top_cand_partido, 'fa-user')}
                {crear_col('TOP PARTIDOS', top_partidos, 'fa-flag')}
                {crear_col('CAND. REGIONAL', top_cand_regional, 'fa-globe')}
                {render_tabla_stats('MÉTRICAS', stats_data, 'fa-calculator')}
                {render_tabla_stats('RANGOS', rangos_data, 'fa-layer-group')}
            </div>
            """
            st.markdown(html_metricas, unsafe_allow_html=True)

            # 8. EL MAPA INTERACTIVO
            v_mapa = votos_final.groupby(level=0).agg({'VOTOS': 'sum', 'MUNNOMBRE': 'first'})
            v_mapa.index = v_mapa.index.astype(str)
            mapa_final = municipios.join(v_mapa[['VOTOS', 'MUNNOMBRE']], how='left')

            if not mapa_final.empty:
                num_unique = mapa_final['VOTOS'].dropna().nunique()
                
                if num_unique < 2:
                    m = mapa_final.explore(
                        column="VOTOS",
                        cmap=dropdown_tema,
                        tooltip=["MUNNOMBRE", "VOTOS"],
                        popup=True,
                        missing_kwds={"color": "#FFFFFF", "label": "Sin votos", "edgecolor": "#686f79"},
                        style_kwds={"fillOpacity": 1.0, "weight": 0.3, "color": "#686f79"},
                        legend=True
                    )
                else:
                    k_val = int(min(40, num_unique))
                    m = mapa_final.explore(
                        column="VOTOS",
                        cmap=dropdown_tema,
                        scheme="NaturalBreaks", 
                        k=k_val,
                        tooltip=["MUNNOMBRE", "VOTOS"],
                        popup=True,
                        missing_kwds={"color": "#FFFFFF", "label": "Sin votos", "edgecolor": "#686f79"},
                        style_kwds={"fillOpacity": 1.0, "weight": 0.3, "color": "#686f79"},
                        legend=True
                    )
                st_folium(m, width=1300, height=600, returned_objects=[])

            # 9. REPORTE IA (Se muestra debajo del mapa automáticamente)
            texto_simulado = f"""
            <p>Basado en los datos analizados para la candidatura de <b>{dropdown_can}</b> del partido <b>{dropdown_par}</b> en la corporación <b>{dropdown_cor}</b>, se observan las siguientes tendencias estratégicas:</p>
            <p>1. <b>Concentración Geográfica:</b> Se evidencia un fuerte peso electoral en los municipios principales, lo que sugiere un voto de opinión o estructura consolidada en cascos urbanos.</p>
            <p>2. <b>Oportunidades de Crecimiento:</b> Existen zonas periféricas con alto potencial donde el partido tiene fuerza, pero la candidatura específica aún no capta ese electorado.</p>
            """
            
            st.markdown(f"""
                <div class="ia-report-container">
                    <span class="ia-badge">ANÁLISIS ESTRATÉGICO DE DATOS</span>
                    <p class="card-title" style="margin-top:0; border:none; text-align:left; font-size: 12px; color: #111827;">
                        <i class="fa fa-terminal"></i> SERPA-AI CONSULTING
                    </p>
                    <div class="ia-text">
                        {texto_simulado}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("⚠️ No hay datos registrados para esta combinación exacta de filtros. Intenta cambiar de candidato o de partido.")
