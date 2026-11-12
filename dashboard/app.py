# Dashboard del monitor de anomalias de afluencia del Metro CDMX: resumen,
# mapa (calor / columnas 3D / puntos), explorador por estacion con el
# pronostico de Prophet, riesgo futuro (XGBoost + Prophet), causas OSINT y
# conexion con ArcGIS Online. Contexto de los datos: dashboard/ANALISIS.md.
#
# Solo lee archivos que estan en el repo (dashboard/data/*.parquet, que genera
# dashboard/preparar_datos.py), asi que se puede desplegar tal cual en
# Streamlit Community Cloud.
#
# Correr con la raiz del repo como working directory:
#   streamlit run dashboard/app.py

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import requests
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
DATOS = BASE / 'data'

# ArcGIS Online: enlace del mapa web / dashboard compartido como PUBLICO (lo ve cualquier visitante)
# y, opcional, URL de una capa de servicio (.../FeatureServer/0) que se dibuja sobre el mapa del dashboard.
# Tambien se pueden definir en los Secrets de Streamlit Cloud como arcgis_url / arcgis_capa.
ARCGIS_URL = 'https://ipn-upiita.maps.arcgis.com/apps/mapviewer/index.html?webmap=7e269609115e4ac082242b3e4259afb5&center=-99.116609%2C19.383384&scale=144447.638572'
ARCGIS_CAPA = ''

NARANJA = '#F26522'
NARANJA_CLARO = '#F9A66C'
GRIS_OSCURO = '#2E2E2E'
GRIS = '#5F6368'
GRIS_CLARO = '#E6E6E6'
FUENTE = 'Inter, "Segoe UI", Roboto, sans-serif'

# Colores de cada linea del Metro (aproximados a la senaletica)
COLORES_LINEA = {
    'linea 1': '#E9468F', 'linea 2': '#0060A9', 'linea 3': '#B5A100', 'linea 4': '#6CC3C1',
    'linea 5': '#F4D000', 'linea 6': '#E1251B', 'linea 7': '#F47B20', 'linea 8': '#00954F',
    'linea 9': '#6B3D2E', 'linea a': '#93268F', 'linea b': '#8A9A8E', 'linea 12': '#C2A05B',
}
COLORES_PRIORIDAD = {
    'CRÍTICA (Consenso)': '#B71C1C', 'ALTA (Solo Prophet)': NARANJA,
    'MEDIA (Solo MAD)': '#F2C14E', 'CIERRE (Operativo)': '#9E9E9E',
}
ANOMALIAS = ['CRÍTICA (Consenso)', 'ALTA (Solo Prophet)', 'MEDIA (Solo MAD)']
DIAS_ES = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
MESES_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

st.set_page_config(page_title='Monitor de anomalías · Metro CDMX', layout='wide')

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; }}
.encabezado {{ background: linear-gradient(90deg, {GRIS_OSCURO} 0%, #444 100%); border-bottom: 6px solid {NARANJA};
  border-radius: 12px; padding: 18px 26px; color: #fff; margin-bottom: 18px; display: flex; align-items: center; gap: 18px; }}
.encabezado .logo {{ min-width: 54px; height: 54px; border-radius: 14px; background: {NARANJA}; display: flex;
  align-items: center; justify-content: center; font-weight: 800; font-size: 28px; color: #fff; }}
.encabezado h1 {{ font-size: 1.55rem; margin: 0; padding: 0; color: #fff; font-weight: 700; }}
.encabezado p {{ margin: 2px 0 0 0; color: #D0D0D0; font-size: 0.9rem; }}
.kpi {{ background: #fff; border-radius: 10px; padding: 14px 16px; border-left: 5px solid {NARANJA};
  box-shadow: 0 1px 4px rgba(0,0,0,.08); height: 100%; }}
.kpi .l {{ font-size: .74rem; color: {GRIS}; text-transform: uppercase; letter-spacing: .05em; }}
.kpi .v {{ font-size: 1.65rem; font-weight: 700; color: {GRIS_OSCURO}; line-height: 1.3; }}
.kpi .s {{ font-size: .8rem; color: {NARANJA}; }}
.seccion {{ font-size: 1.05rem; font-weight: 700; color: {GRIS_OSCURO}; border-left: 4px solid {NARANJA};
  padding-left: 10px; margin: 14px 0 6px 0; }}
.nota {{ font-size: .82rem; color: {GRIS}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ background: {GRIS_CLARO}; border-radius: 8px 8px 0 0; padding: 8px 18px; }}
.stTabs [aria-selected="true"] {{ background: {NARANJA} !important; color: #fff !important; }}
.stTabs [aria-selected="true"] p {{ color: #fff !important; }}
</style>
""", unsafe_allow_html=True)


def nombre_linea(linea):
    return 'Línea ' + str(linea).split()[-1].upper()


def nombre_estacion(estacion):
    return ' '.join(p if p in ('de', 'del', 'la', 'las', 'los', 'y') else p.capitalize() for p in str(estacion).split())


def kpi(columna, etiqueta, valor, sub=''):
    columna.markdown(f'<div class="kpi"><div class="l">{etiqueta}</div><div class="v">{valor}</div>'
                     f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def seccion(texto):
    st.markdown(f'<div class="seccion">{texto}</div>', unsafe_allow_html=True)


def estilo(fig, alto=360, titulo=None):
    fig.update_layout(template='plotly_white', height=alto, title=titulo, margin=dict(l=10, r=10, t=45 if titulo else 10, b=10),
                      font=dict(family=FUENTE, color=GRIS_OSCURO, size=12), title_font=dict(size=15, color=GRIS_OSCURO),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, title=None),
                      hoverlabel=dict(font_family=FUENTE))
    return fig


def hex_rgb(color, alfa=220):
    color = color.lstrip('#')
    return [int(color[i:i + 2], 16) for i in (0, 2, 4)] + [alfa]


@st.cache_data(show_spinner='Cargando datos…')
def cargar():
    series = pd.read_parquet(DATOS / 'series_estaciones.parquet')
    for col in ['linea', 'estacion']:
        series[col] = series[col].astype(str)
    series['prioridad_auditoria'] = series['prioridad_auditoria'].astype(object)
    series['impacto'] = series['afluencia'] - series['yhat']
    coords = pd.read_csv(BASE / 'estaciones_coordenadas.csv')
    top = pd.read_parquet(DATOS / 'riesgo_top_estaciones.parquet')
    alerta = pd.read_parquet(DATOS / 'riesgo_dias_alerta.parquet')
    bitacora = pd.read_csv(REPO / 'bitacora_investigacion_anomalias_criticas.csv')
    bitacora.columns = bitacora.columns.str.lower()
    bitacora['fecha'] = pd.to_datetime(bitacora['fecha'])
    bitacora['causa'] = bitacora['hallazgo_principal'].str.split('(').str[0].str.strip()
    return series, coords, top, alerta, bitacora


@st.cache_data(show_spinner='Descargando capa de ArcGIS…', ttl=3600)
def capa_arcgis(url):
    url = url.rstrip('/')
    if not url.endswith('/query'):
        url += '/query'
    r = requests.get(url, params={'where': '1=1', 'outFields': '*', 'outSR': 4326, 'f': 'geojson'}, timeout=30)
    r.raise_for_status()
    datos = r.json()
    if 'features' not in datos:
        raise ValueError(datos.get('error', {}).get('message', 'La respuesta no es GeoJSON'))
    return datos


faltan = [p for p in [DATOS / 'series_estaciones.parquet', DATOS / 'riesgo_top_estaciones.parquet',
                      REPO / 'bitacora_investigacion_anomalias_criticas.csv'] if not p.exists()]
if faltan:
    st.error('Faltan datos del dashboard: ' + ', '.join(str(p.relative_to(REPO)) for p in faltan) +
             '. Corre `python dashboard/preparar_datos.py` desde la raíz del repo.')
    st.stop()

series, coords, top, alerta, bitacora = cargar()


def config_arcgis(clave, valor):
    # Constante del codigo primero; si esta vacia, Secrets de Streamlit (si existen)
    if valor:
        return valor
    try:
        return st.secrets.get(clave, '')
    except Exception:
        return ''


arcgis_url = config_arcgis('arcgis_url', ARCGIS_URL)
arcgis_capa = config_arcgis('arcgis_capa', ARCGIS_CAPA)
hist = series[~series['es_futuro']]
futuro = series[series['es_futuro']]

st.markdown(f"""
<div class="encabezado"><div class="logo">M</div><div>
<h1>Monitor de anomalías de afluencia · Metro CDMX</h1>
<p>Detección con Prophet + MAD, investigación OSINT y riesgo futuro con XGBoost · Datos abiertos SEMOVI
{hist['fecha'].min():%d/%m/%Y} – {hist['fecha'].max():%d/%m/%Y}</p></div></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- filtros globales
with st.sidebar:
    st.markdown(f'<div class="seccion">Filtros</div>', unsafe_allow_html=True)
    f_min, f_max = hist['fecha'].min().date(), hist['fecha'].max().date()
    rango = st.date_input('Periodo', (f_min, f_max), min_value=f_min, max_value=f_max)
    lineas = sorted(hist['linea'].unique(), key=lambda l: (len(l), l))
    lineas_sel = st.multiselect('Líneas', lineas, default=lineas, format_func=nombre_linea)
    prioridades_sel = st.multiselect('Tipo de anomalía', ANOMALIAS, default=['CRÍTICA (Consenso)'])
    st.markdown('<p class="nota">CRÍTICA: Prophet y MAD coinciden. ALTA: solo Prophet. MEDIA: solo MAD. '
                'Los cierres operativos no cuentan como anomalía.</p>', unsafe_allow_html=True)

inicio, fin = (pd.Timestamp(rango[0]), pd.Timestamp(rango[1])) if isinstance(rango, tuple) and len(rango) == 2 \
    else (pd.Timestamp(f_min), pd.Timestamp(f_max))
hist_f = hist[hist['fecha'].between(inicio, fin) & hist['linea'].isin(lineas_sel)]
anom_f = hist_f[hist_f['prioridad_auditoria'].isin(prioridades_sel)]

tab_resumen, tab_mapa, tab_estacion, tab_riesgo, tab_osint, tab_arcgis = st.tabs(
    ['Resumen', 'Mapa', 'Estación', 'Riesgo próximo', 'Causas (OSINT)', 'ArcGIS'])

# ---------------------------------------------------------------- resumen
with tab_resumen:
    validos = hist_f[~hist_f['prioridad_auditoria'].eq('CIERRE (Operativo)')]
    criticas = hist_f['prioridad_auditoria'].eq('CRÍTICA (Consenso)').sum()
    explicadas = 1 - bitacora['causa'].eq('Falsa Alarma').mean()
    c = st.columns(5)
    kpi(c[0], 'Estación-días analizados', f'{len(hist_f):,}', f'{hist_f["estacion"].nunique()} estaciones · {len(lineas_sel)} líneas')
    kpi(c[1], 'Anomalías seleccionadas', f'{len(anom_f):,}', f'{len(anom_f) / max(len(validos), 1):.1%} de los días operativos')
    kpi(c[2], 'Anomalías críticas', f'{criticas:,}', f'{criticas / max(len(validos), 1):.1%} de los días operativos')
    kpi(c[3], 'Cierres operativos', f'{hist_f["prioridad_auditoria"].eq("CIERRE (Operativo)").sum():,}', 'no cuentan como anomalía')
    kpi(c[4], 'Explicadas con OSINT', f'{explicadas:.0%}', f'de {len(bitacora)} críticas investigadas')

    mensual = (hist_f[hist_f['prioridad_auditoria'].isin(ANOMALIAS)]
               .groupby([pd.Grouper(key='fecha', freq='MS'), 'prioridad_auditoria']).size().reset_index(name='n'))
    fig = px.bar(mensual, x='fecha', y='n', color='prioridad_auditoria', color_discrete_map=COLORES_PRIORIDAD,
                 labels={'fecha': '', 'n': 'Estación-días', 'prioridad_auditoria': ''})
    st.plotly_chart(estilo(fig, 380, 'Anomalías por mes y tipo'))

    izq, der = st.columns([1, 1])
    with izq:
        por_linea = (anom_f.groupby('linea').size().reindex(lineas_sel).fillna(0).reset_index(name='n'))
        por_linea['nombre'] = por_linea['linea'].map(nombre_linea)
        fig = px.bar(por_linea, x='nombre', y='n', color='linea', color_discrete_map=COLORES_LINEA,
                     labels={'nombre': '', 'n': 'Anomalías seleccionadas'})
        fig.update_layout(showlegend=False)
        st.plotly_chart(estilo(fig, 340, 'Anomalías seleccionadas por línea'))
    with der:
        tasa = (validos.assign(anio=validos['fecha'].dt.year, mes=validos['fecha'].dt.month,
                               es=validos['prioridad_auditoria'].isin(prioridades_sel))
                .pivot_table(index='anio', columns='mes', values='es', aggfunc='mean') * 100)
        fig = go.Figure(go.Heatmap(z=tasa.values, x=[MESES_ES[m - 1] for m in tasa.columns], y=tasa.index.astype(str),
                                   colorscale=[[0, '#FFFFFF'], [.5, NARANJA_CLARO], [1, '#B71C1C']],
                                   hovertemplate='%{y} %{x}: %{z:.2f}% de estación-días<extra></extra>',
                                   colorbar=dict(title='%')))
        st.plotly_chart(estilo(fig, 340, 'Calendario: % de estación-días con anomalía'))

# ---------------------------------------------------------------- mapa
with tab_mapa:
    c1, c2, c3 = st.columns([1.3, 1.3, 1])
    metrica = c1.selectbox('Indicador', ['Anomalías seleccionadas', 'Afluencia diaria mediana', 'Impacto promedio (pasajeros)'])
    vista = c2.radio('Visualización', ['Mapa de calor', 'Columnas 3D', 'Puntos por línea'], horizontal=True)
    fondo = c3.radio('Fondo', ['Oscuro', 'Claro'], horizontal=True)

    por_est = (hist_f[~hist_f['prioridad_auditoria'].eq('CIERRE (Operativo)')].groupby(['linea', 'estacion'])
               .agg(afluencia=('afluencia', 'median')).join(
                   anom_f.groupby(['linea', 'estacion']).agg(anomalias=('fecha', 'size'), impacto=('impacto', 'mean')))
               .fillna({'anomalias': 0}).reset_index().merge(coords, on=['linea', 'estacion']))
    col = {'Anomalías seleccionadas': 'anomalias', 'Afluencia diaria mediana': 'afluencia',
           'Impacto promedio (pasajeros)': 'impacto'}[metrica]
    por_est['valor'] = por_est[col].abs().fillna(0) if col == 'impacto' else por_est[col].fillna(0)
    por_est['nombre'] = por_est['estacion'].map(nombre_estacion)
    por_est['nombre_linea'] = por_est['linea'].map(nombre_linea)
    por_est['color'] = por_est['linea'].map(lambda l: hex_rgb(COLORES_LINEA.get(l, GRIS)))
    maximo = max(por_est['valor'].max(), 1)
    por_est['intensidad'] = por_est['valor'] / maximo
    por_est['color_int'] = por_est['intensidad'].map(
        lambda t: [int(255 - 30 * t), int(200 - 170 * t), int(120 - 110 * t), 230])
    por_est['texto'] = por_est.apply(lambda r: f"{r['afluencia']:,.0f}" if col == 'afluencia' else
                                     (f"{r['anomalias']:,.0f}" if col == 'anomalias' else f"{r['impacto']:,.0f}"), axis=1)

    capas = []
    if vista == 'Mapa de calor':
        capas.append(pdk.Layer('HeatmapLayer', data=por_est, get_position='[lon, lat]', get_weight='valor',
                               radius_pixels=55, intensity=1.2, threshold=0.04, aggregation='SUM',
                               color_range=[[255, 237, 213], [253, 190, 133], [253, 141, 60], [242, 101, 34], [217, 72, 1], [140, 20, 20]]))
        capas.append(pdk.Layer('ScatterplotLayer', data=por_est, get_position='[lon, lat]', get_radius=90,
                               get_fill_color=[255, 255, 255, 160], pickable=True))
        pitch = 0
    elif vista == 'Columnas 3D':
        capas.append(pdk.Layer('ColumnLayer', data=por_est, get_position='[lon, lat]', get_elevation='intensidad',
                               elevation_scale=5500, radius=230, get_fill_color='color_int', pickable=True, auto_highlight=True,
                               extruded=True))
        pitch = 50
    else:
        capas.append(pdk.Layer('ScatterplotLayer', data=por_est, get_position='[lon, lat]', get_fill_color='color',
                               get_radius=f'80 + 520 * intensidad', get_line_color=[255, 255, 255], line_width_min_pixels=1,
                               stroked=True, pickable=True, auto_highlight=True))
        pitch = 0
    if arcgis_capa and st.checkbox('Mostrar capa de ArcGIS', value=True):
        try:
            capas.append(pdk.Layer('GeoJsonLayer', data=capa_arcgis(arcgis_capa), stroked=True, filled=True,
                                   get_fill_color=[242, 101, 34, 60], get_line_color=[242, 101, 34, 220],
                                   line_width_min_pixels=2, point_radius_min_pixels=4, pickable=False))
        except Exception as e:
            st.warning(f'No se pudo cargar la capa de ArcGIS: {e}')
    deck = pdk.Deck(layers=capas, map_provider='carto',
                    map_style=pdk.map_styles.CARTO_DARK if fondo == 'Oscuro' else pdk.map_styles.CARTO_LIGHT,
                    initial_view_state=pdk.ViewState(latitude=19.41, longitude=-99.13, zoom=10.6, pitch=pitch, bearing=-10 if pitch else 0),
                    tooltip={'html': '<b>{nombre}</b><br/>{nombre_linea}<br/>' + metrica + ': <b>{texto}</b>',
                             'style': {'backgroundColor': GRIS_OSCURO, 'color': 'white', 'fontFamily': FUENTE}})
    st.pydeck_chart(deck, height=600)
    st.markdown(f'<p class="nota">{len(por_est)} estaciones con coordenada · periodo {inicio:%d/%m/%Y} – {fin:%d/%m/%Y}. '
                'Coordenadas de una fuente de terceros, pendientes de validar contra la capa oficial (ver pestaña ArcGIS).</p>',
                unsafe_allow_html=True)

    seccion(f'Estaciones con mayor valor · {metrica.lower()}')
    tabla = por_est.sort_values('valor', ascending=False).head(15)
    st.dataframe(tabla[['nombre', 'nombre_linea', 'anomalias', 'afluencia', 'impacto']], hide_index=True,
                 column_config={'nombre': 'Estación', 'nombre_linea': 'Línea',
                                'anomalias': st.column_config.ProgressColumn('Anomalías', format='%d', min_value=0,
                                                                             max_value=float(max(por_est['anomalias'].max(), 1))),
                                'afluencia': st.column_config.NumberColumn('Afluencia diaria mediana', format='%,.0f'),
                                'impacto': st.column_config.NumberColumn('Impacto promedio', format='%,.0f')})

# ---------------------------------------------------------------- estacion
with tab_estacion:
    c1, c2, c3 = st.columns([1, 2, 1.2])
    linea_e = c1.selectbox('Línea', lineas, format_func=nombre_linea, key='linea_e')
    estaciones = sorted(hist.loc[hist['linea'] == linea_e, 'estacion'].unique())
    est_e = c2.selectbox('Estación', estaciones, format_func=nombre_estacion, key='est_e')
    ventana = c3.radio('Ventana', ['Último año + pronóstico', 'Todo'], horizontal=True)

    s = series[(series['linea'] == linea_e) & (series['estacion'] == est_e)].sort_values('fecha')
    sh, sf = s[~s['es_futuro']], s[s['es_futuro']]
    riesgo_est = top[(top['linea'] == linea_e) & (top['estacion'] == est_e)]
    c = st.columns(5)
    kpi(c[0], 'Afluencia diaria mediana', f'{sh.loc[~sh["prioridad_auditoria"].eq("CIERRE (Operativo)"), "afluencia"].median():,.0f}', 'pasajeros')
    kpi(c[1], 'Anomalías críticas', f'{sh["prioridad_auditoria"].eq("CRÍTICA (Consenso)").sum():,}',
        f'{sh["prioridad_auditoria"].isin(ANOMALIAS).sum():,} anomalías de cualquier tipo')
    kpi(c[2], 'Días de cierre', f'{sh["prioridad_auditoria"].eq("CIERRE (Operativo)").sum():,}', 'cierres operativos')
    kpi(c[3], 'Pronóstico próximo mes', f'{sf["yhat"].head(30).mean():,.0f}', 'pasajeros diarios esperados')
    kpi(c[4], 'Riesgo futuro', f'{riesgo_est["riesgo_promedio"].iloc[0]:.2f}x' if len(riesgo_est) else 'Normal',
        f'puesto {int(riesgo_est["ranking"].iloc[0])} de 30' if len(riesgo_est) else 'fuera del top 30')

    if ventana != 'Todo':
        sh = sh[sh['fecha'] > sh['fecha'].max() - pd.Timedelta(days=365)]
    fig = go.Figure()
    for tramo, color, nombre in [(sh, 'rgba(95,99,104,0.18)', 'Rango esperado (Prophet 95%)'),
                                 (sf, 'rgba(242,101,34,0.22)', 'Rango pronosticado')]:
        fig.add_trace(go.Scatter(x=pd.concat([tramo['fecha'], tramo['fecha'][::-1]]),
                                 y=pd.concat([tramo['yhat_upper'], tramo['yhat_lower'][::-1]]),
                                 fill='toself', fillcolor=color, line=dict(width=0), name=nombre, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=sh['fecha'], y=sh['yhat'], name='Esperado (Prophet)', line=dict(color=GRIS, width=1, dash='dot')))
    fig.add_trace(go.Scatter(x=sh['fecha'], y=sh['afluencia'], name='Afluencia real', line=dict(color=GRIS_OSCURO, width=1.4)))
    fig.add_trace(go.Scatter(x=sf['fecha'], y=sf['yhat'], name='Pronóstico', line=dict(color=NARANJA, width=2)))
    for prioridad, color in COLORES_PRIORIDAD.items():
        p = sh[sh['prioridad_auditoria'] == prioridad]
        if len(p):
            fig.add_trace(go.Scatter(x=p['fecha'], y=p['afluencia'], mode='markers', name=prioridad,
                                     marker=dict(color=color, size=7 if prioridad.startswith('CRÍTICA') else 5,
                                                 line=dict(color='white', width=.5)),
                                     customdata=p[['yhat', 'impacto']].values,
                                     hovertemplate='%{x|%d/%m/%Y}<br>Real: %{y:,.0f}<br>Esperado: %{customdata[0]:,.0f}'
                                                   '<br>Diferencia: %{customdata[1]:+,.0f}<extra>' + prioridad + '</extra>'))
    fig.update_yaxes(tickformat=',', title='Pasajeros por día')
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=.06))
    st.plotly_chart(estilo(fig, 520, f'{nombre_estacion(est_e)} · {nombre_linea(linea_e)}: afluencia real, esperada y pronóstico'))

    izq, der = st.columns([1.3, 1])
    with izq:
        seccion('Anomalías críticas más recientes')
        ult = s[s['prioridad_auditoria'].eq('CRÍTICA (Consenso)')].sort_values('fecha', ascending=False).head(12)
        st.dataframe(ult.assign(fecha=ult['fecha'].dt.date)[['fecha', 'afluencia', 'yhat', 'impacto']], hide_index=True,
                     column_config={'fecha': 'Fecha', 'afluencia': st.column_config.NumberColumn('Real', format='%,.0f'),
                                    'yhat': st.column_config.NumberColumn('Esperado', format='%,.0f'),
                                    'impacto': st.column_config.NumberColumn('Diferencia', format='%+,.0f')})
    with der:
        seccion('Causas encontradas con OSINT en esta estación')
        b = bitacora[(bitacora['linea'] == linea_e) & (bitacora['estacion'] == est_e)]
        if len(b):
            st.dataframe(b.sort_values('fecha', ascending=False).assign(fecha=b['fecha'].dt.date)[['fecha', 'causa', 'descripcion_incidente']],
                         hide_index=True, column_config={'fecha': 'Fecha', 'causa': 'Causa', 'descripcion_incidente': 'Descripción'})
        else:
            st.info('Esta estación no salió en la muestra investigada con OSINT.')

# ---------------------------------------------------------------- riesgo futuro
with tab_riesgo:
    st.markdown('<p class="nota">Modelo XGBoost apoyado en el pronóstico de Prophet: estima para cada estación-día futuro la '
                'probabilidad de una anomalía CRÍTICA. "Riesgo" compara contra un día típico del mismo día de la semana '
                '(1.0x = normal, 2.0x = el doble). Sirve para priorizar vigilancia, no como predictor exacto de fallas.</p>',
                unsafe_allow_html=True)
    dias = alerta.groupby('fecha').agg(estaciones=('estacion', 'size'), riesgo=('riesgo_vs_mismo_dia', 'mean')).reset_index()
    pico = dias.sort_values('estaciones', ascending=False).iloc[0]
    c = st.columns(4)
    kpi(c[0], 'Horizonte', f'{futuro["fecha"].min():%d/%m/%y} – {futuro["fecha"].max():%d/%m/%y}', 'pronóstico de Prophet')
    kpi(c[1], 'Estaciones prioritarias', f'{len(top)}', 'mayor riesgo promedio')
    kpi(c[2], 'Días en alerta', f'{len(alerta):,}', 'estación-días con riesgo ≥ 2x')
    kpi(c[3], 'Fecha más crítica', f'{pico["fecha"]:%d/%m/%Y}', f'{pico["estaciones"]} estaciones en alerta')

    izq, der = st.columns([1.3, 1])
    with izq:
        t = top.head(15).iloc[::-1].copy()
        t['etiqueta'] = t['estacion'].map(nombre_estacion) + ' · ' + t['linea'].map(lambda l: 'L' + l.split()[-1].upper())
        fig = px.bar(t, x='riesgo_promedio', y='etiqueta', orientation='h', color='riesgo_promedio',
                     color_continuous_scale=[[0, NARANJA_CLARO], [1, '#B71C1C']], text=t['riesgo_promedio'].map('{:.2f}x'.format),
                     custom_data=['dias_en_alerta', 'fecha_pico'],
                     labels={'riesgo_promedio': 'Riesgo promedio', 'etiqueta': ''})
        fig.update_traces(textposition='outside', hovertemplate='%{y}<br>Riesgo %{x:.2f}x<br>%{customdata[0]} días en alerta'
                                                                  '<br>Pico: %{customdata[1]}<extra></extra>')
        fig.add_vline(x=1, line_dash='dash', line_color=GRIS)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(estilo(fig, 520, 'Top 15 estaciones con mayor riesgo'))
    with der:
        seccion('Fechas con más estaciones en alerta')
        prox = dias.sort_values('estaciones', ascending=False).head(12).sort_values('fecha')
        st.dataframe(prox.assign(dia=prox['fecha'].dt.day_of_week.map(DIAS_ES), fecha=prox['fecha'].dt.date)[['fecha', 'dia', 'estaciones', 'riesgo']],
                     hide_index=True, height=470,
                     column_config={'fecha': 'Fecha', 'dia': 'Día',
                                    'estaciones': st.column_config.ProgressColumn('Estaciones en alerta', format='%d', min_value=0, max_value=30),
                                    'riesgo': st.column_config.NumberColumn('Riesgo promedio', format='%.1fx')})

    seccion('Calendario de alertas: estaciones en alerta por día')
    cal = dias.set_index('fecha')['estaciones'].reindex(pd.date_range(futuro['fecha'].min(), futuro['fecha'].max()), fill_value=0)
    semana = ((cal.index - cal.index[0]).days + cal.index[0].day_of_week) // 7
    lunes = cal.index - pd.to_timedelta(cal.index.day_of_week, unit='D')
    grid = pd.DataFrame({'semana': semana, 'dia': cal.index.day_of_week, 'n': cal.values, 'fecha': cal.index})
    z = grid.pivot(index='dia', columns='semana', values='n')
    fechas_txt = grid.pivot(index='dia', columns='semana', values='fecha').apply(lambda c: c.dt.strftime('%d/%m/%Y'))
    etiquetas_x = pd.Series(lunes).groupby(semana).first().dt.strftime('%d %b')
    fig = go.Figure(go.Heatmap(z=z.values, x=etiquetas_x.values, y=[DIAS_ES[d] for d in z.index], text=fechas_txt.values,
                               colorscale=[[0, '#F4F4F4'], [.15, '#FDD9BF'], [.5, NARANJA], [1, '#8C1414']], xgap=3, ygap=3,
                               hovertemplate='%{text}: %{z} estaciones en alerta<extra></extra>', colorbar=dict(title='Est.')))
    fig.update_yaxes(autorange='reversed')
    st.plotly_chart(estilo(fig, 300))

# ---------------------------------------------------------------- OSINT
with tab_osint:
    b = bitacora.copy()
    b['impacto_abs'] = b['impacto_pasajeros'].abs()
    oculta = b['causa'].eq('Falla Oculta')
    c = st.columns(4)
    kpi(c[0], 'Anomalías investigadas', f'{len(b)}', 'muestra estratificada (95% confianza)')
    kpi(c[1], 'Con causa identificada', f'{1 - b["causa"].eq("Falsa Alarma").mean():.0%}', 'el resto: falsa alarma')
    kpi(c[2], 'Fallas ocultas', f'{oculta.mean():.1%}', f'{b.loc[oculta, "impacto_abs"].sum():,.0f} pasajeros afectados')
    kpi(c[3], 'Causa más frecuente', b['causa'].value_counts().index[0].split('/')[0].strip(), f'{b["causa"].value_counts().iloc[0]} registros')

    izq, der = st.columns(2)
    with izq:
        causas = b['causa'].value_counts().iloc[::-1].reset_index()
        causas.columns = ['causa', 'n']
        causas['color'] = causas['causa'].map(lambda x: '#B71C1C' if x == 'Falla Oculta' else (GRIS if x == 'Falsa Alarma' else NARANJA))
        fig = go.Figure(go.Bar(x=causas['n'], y=causas['causa'], orientation='h', marker_color=causas['color'],
                               text=(causas['n'] / causas['n'].sum()).map('{:.1%}'.format), textposition='outside'))
        st.plotly_chart(estilo(fig, 440, 'Causas de las anomalías críticas'))
    with der:
        orden = b.groupby('causa')['impacto_abs'].median().sort_values().index
        fig = px.box(b, x='impacto_abs', y='causa', category_orders={'causa': list(orden)}, points='all',
                     color_discrete_sequence=[NARANJA], labels={'impacto_abs': 'Pasajeros afectados (valor absoluto)', 'causa': ''})
        fig.update_xaxes(type='log')
        st.plotly_chart(estilo(fig, 440, 'Severidad del impacto por causa'))

    seccion('Matriz de vulnerabilidad: estaciones con más anomalías investigadas')
    top_est = b.groupby(['linea', 'estacion']).size().sort_values(ascending=False).head(18).index
    m = b.set_index(['linea', 'estacion']).loc[top_est].reset_index()
    m['nombre'] = m['estacion'].map(nombre_estacion) + ' · L' + m['linea'].str.split().str[-1].str.upper()
    piv = pd.crosstab(m['nombre'], m['causa'])
    piv = piv.loc[piv.sum(axis=1).sort_values().index]
    fig = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=piv.index, colorscale=[[0, '#FFFFFF'], [.3, NARANJA_CLARO], [1, '#B71C1C']],
                               xgap=2, ygap=2, hovertemplate='%{y}<br>%{x}: %{z}<extra></extra>', showscale=False,
                               text=piv.values, texttemplate='%{text}'))
    st.plotly_chart(estilo(fig, 520))

    seccion('Estacionalidad de las causas')
    est = pd.crosstab(b['causa'], b['fecha'].dt.month).reindex(columns=range(1, 13), fill_value=0)
    fig = go.Figure(go.Heatmap(z=est.values, x=MESES_ES, y=est.index, colorscale=[[0, '#FFFFFF'], [.3, NARANJA_CLARO], [1, '#B71C1C']],
                               xgap=2, ygap=2, text=est.values, texttemplate='%{text}', showscale=False,
                               hovertemplate='%{y}<br>%{x}: %{z}<extra></extra>'))
    st.plotly_chart(estilo(fig, 420))

# ---------------------------------------------------------------- ArcGIS
with tab_arcgis:
    if arcgis_url:
        url = arcgis_url
        if 'webmap=' in url and 'embed' not in url.lower():
            url = 'https://www.arcgis.com/apps/Embed/index.html?webmap=' + url.split('webmap=')[1].split('&')[0]
        seccion('Mapa del proyecto en ArcGIS Online')
        if hasattr(st, 'iframe'):
            st.iframe(url, height=720)
        else:   # versiones de Streamlit anteriores a st.iframe
            components.iframe(url, height=720, scrolling=True)
        st.markdown(f'<p class="nota">Si el mapa no carga, ábrelo directamente: <a href="{arcgis_url}" target="_blank">'
                    'ver en ArcGIS Online</a>.</p>', unsafe_allow_html=True)
    else:
        st.info('Aún no hay un mapa de ArcGIS configurado. Pon el enlace del mapa web o dashboard (compartido como '
                'público) en la constante ARCGIS_URL al inicio de dashboard/app.py, o en los Secrets de Streamlit Cloud '
                'como arcgis_url.')

st.markdown(f'<p class="nota" style="text-align:center;margin-top:24px">Trabajo Terminal 2026-B125 · Datos abiertos de SEMOVI '
            f'(datos.cdmx.gob.mx) · Proyecto académico, no es un sitio oficial del STC Metro.</p>', unsafe_allow_html=True)
