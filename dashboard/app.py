# Dashboard del monitor de anomalias de afluencia del Metro CDMX, pensado para
# usuarios: mapa de ArcGIS Online con el ranking de estaciones por afluencia o
# anomalias, y series de tiempo por estacion (real, esperado por Prophet y
# pronostico).
# Contexto de los datos: dashboard/ANALISIS.md.
#
# Solo lee archivos que estan en el repo (dashboard/data/*.parquet, que genera
# dashboard/preparar_datos.py), asi que se puede desplegar tal cual en
# Streamlit Community Cloud.
#
# Correr con la raiz del repo como working directory:
#   streamlit run dashboard/app.py

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
DATOS = BASE / 'data'

# ArcGIS Online: enlace del mapa web / dashboard compartido como PUBLICO (lo ve cualquier visitante).
# Tambien se puede definir en los Secrets de Streamlit Cloud como arcgis_url.
ARCGIS_URL = 'https://ipn-upiita.maps.arcgis.com/apps/mapviewer/index.html?webmap=7e269609115e4ac082242b3e4259afb5&center=-99.116609%2C19.383384&scale=144447.638572'

NARANJA = '#F26522'
NARANJA_CLARO = '#F9A66C'
ROJO = '#B71C1C'
GRIS_OSCURO = '#2E2E2E'
GRIS = '#5F6368'
GRIS_CLARO = '#E6E6E6'
FUENTE = 'Inter, "Segoe UI", Roboto, sans-serif'

CRITICA = 'CRÍTICA (Consenso)'
MENORES = ['ALTA (Solo Prophet)', 'MEDIA (Solo MAD)']
CIERRE = 'CIERRE (Operativo)'
PERIODOS = {'Último año': 365, 'Últimos 3 meses': 91, 'Todo el histórico': None}

st.set_page_config(page_title='Monitor de anomalías · Metro CDMX', layout='wide')

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
.encabezado {{ background: linear-gradient(90deg, {GRIS_OSCURO} 0%, #474747 100%); border-bottom: 6px solid {NARANJA};
  border-radius: 12px; padding: 20px 28px; color: #fff; margin-bottom: 16px; display: flex; align-items: center; gap: 18px; }}
.encabezado .logo {{ min-width: 56px; height: 56px; border-radius: 14px; background: {NARANJA}; display: flex;
  align-items: center; justify-content: center; font-weight: 800; font-size: 30px; color: #fff; }}
.encabezado h1 {{ font-size: 1.6rem; margin: 0; padding: 0; color: #fff; font-weight: 700; }}
.encabezado p {{ margin: 3px 0 0 0; color: #D6D6D6; font-size: 0.95rem; }}
.kpi {{ background: #fff; border-radius: 10px; padding: 14px 18px; border-left: 5px solid {NARANJA};
  box-shadow: 0 1px 4px rgba(0,0,0,.08); height: 100%; }}
.kpi .l {{ font-size: .74rem; color: {GRIS}; text-transform: uppercase; letter-spacing: .05em; }}
.kpi .v {{ font-size: 1.6rem; font-weight: 700; color: {GRIS_OSCURO}; line-height: 1.3; }}
.kpi .s {{ font-size: .8rem; color: {NARANJA}; }}
.seccion {{ font-size: 1.05rem; font-weight: 700; color: {GRIS_OSCURO}; border-left: 4px solid {NARANJA};
  padding-left: 10px; margin: 6px 0 8px 0; }}
.nota {{ font-size: .85rem; color: {GRIS}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ background: {GRIS_CLARO}; border-radius: 8px 8px 0 0; padding: 10px 22px; }}
.stTabs [data-baseweb="tab"] p {{ font-size: 1rem; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: {NARANJA} !important; }}
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


@st.cache_data(show_spinner='Cargando datos…')
def cargar():
    series = pd.read_parquet(DATOS / 'series_estaciones.parquet')
    for col in ['linea', 'estacion']:
        series[col] = series[col].astype(str)
    series['prioridad_auditoria'] = series['prioridad_auditoria'].astype(object)
    series['diferencia'] = series['afluencia'] - series['yhat']
    top = pd.read_parquet(DATOS / 'riesgo_top_estaciones.parquet')
    bitacora = pd.read_csv(REPO / 'bitacora_investigacion_anomalias_criticas.csv')
    bitacora.columns = bitacora.columns.str.lower()
    bitacora['fecha'] = pd.to_datetime(bitacora['fecha']).dt.normalize()
    bitacora['causa'] = bitacora['hallazgo_principal'].str.split('(').str[0].str.strip()
    return series, top, bitacora


def config_arcgis(clave, valor):
    # Constante del codigo primero; si esta vacia, Secrets de Streamlit (si existen)
    if valor:
        return valor
    try:
        return st.secrets.get(clave, '')
    except Exception:
        return ''


faltan = [p for p in [DATOS / 'series_estaciones.parquet', DATOS / 'riesgo_top_estaciones.parquet',
                      REPO / 'bitacora_investigacion_anomalias_criticas.csv'] if not p.exists()]
if faltan:
    st.error('Faltan datos del dashboard: ' + ', '.join(str(p.relative_to(REPO)) for p in faltan) +
             '. Corre `python dashboard/preparar_datos.py` desde la raíz del repo.')
    st.stop()

series, top, bitacora = cargar()
hist = series[~series['es_futuro']]
futuro = series[series['es_futuro']]
ultimo_dato = hist['fecha'].max()
arcgis_url = config_arcgis('arcgis_url', ARCGIS_URL)

estaciones = (hist[['linea', 'estacion']].drop_duplicates()
              .assign(clave=lambda d: d['linea'] + '|' + d['estacion'],
                      orden=lambda d: d['linea'].str.split().str[-1].map(lambda x: (len(x), x)))
              .sort_values(['orden', 'estacion']))
etiqueta_estacion = {r.clave: f'{nombre_estacion(r.estacion)} · {nombre_linea(r.linea)}' for r in estaciones.itertuples()}

st.markdown("""
<div class="encabezado"><div class="logo">M</div><div>
<h1>Monitor de anomalías de afluencia · Metro CDMX</h1>
<p>¿Cuánta gente usa cada estación, qué días se salieron de lo normal y qué se espera en los próximos meses?</p></div></div>
""", unsafe_allow_html=True)

ultimo_anio = hist[hist['fecha'] > ultimo_dato - pd.Timedelta(days=365)]
c = st.columns(4)
kpi(c[0], 'Estaciones monitoreadas', f'{len(estaciones)}', '12 líneas del Metro')
kpi(c[1], 'Datos hasta', f'{ultimo_dato:%d/%m/%Y}', f'desde {hist["fecha"].min():%d/%m/%Y} · SEMOVI')
kpi(c[2], 'Anomalías graves (último año)', f'{ultimo_anio["prioridad_auditoria"].eq(CRITICA).sum():,}',
    'días-estación muy fuera de lo normal')
kpi(c[3], 'Pronóstico hasta', f'{futuro["fecha"].max():%d/%m/%Y}', 'afluencia esperada por estación')
st.write('')

tab_mapa, tab_series = st.tabs(['Mapa', 'Series de tiempo'])

# ---------------------------------------------------------------- mapa (ArcGIS) + ranking de estaciones
with tab_mapa:
    izq, der = st.columns([2.5, 1])
    with izq:
        if arcgis_url:
            if hasattr(st, 'iframe'):
                st.iframe(arcgis_url, height=640)
            else:   # versiones de Streamlit anteriores a st.iframe
                components.iframe(arcgis_url, height=640, scrolling=True)
            st.markdown(f'<p class="nota">Si el mapa no carga, ábrelo directamente: <a href="{arcgis_url}" target="_blank">'
                        'ver en ArcGIS Online</a>.</p>', unsafe_allow_html=True)
        else:
            st.info('Aún no hay un mapa de ArcGIS configurado. Pon el enlace del mapa web (compartido como público) en '
                    'la constante ARCGIS_URL al inicio de dashboard/app.py, o en los Secrets de Streamlit Cloud como arcgis_url.')

    with der:
        ver = st.radio('Ver', ['Afluencia', 'Anomalías'], horizontal=True)
        periodo = st.selectbox('Periodo', list(PERIODOS), key='periodo_mapa')
        menores = ver == 'Anomalías' and st.toggle(
            'Incluir anomalías leves', value=False,
            help='Por defecto solo se cuentan las graves: días en que el pronóstico (Prophet) y la '
                 'comparación con semanas anteriores (MAD) coinciden en que algo raro pasó.')

        dias = PERIODOS[periodo]
        datos = hist if dias is None else hist[hist['fecha'] > ultimo_dato - pd.Timedelta(days=dias)]
        tipos = [CRITICA] + (MENORES if menores else [])
        por_est = (datos[~datos['prioridad_auditoria'].eq(CIERRE)].groupby(['linea', 'estacion'])
                   .agg(afluencia=('afluencia', 'median'))
                   .join(datos[datos['prioridad_auditoria'].isin(tipos)].groupby(['linea', 'estacion']).size().rename('anomalias'))
                   .fillna({'anomalias': 0}).reset_index())
        por_est['nombre'] = por_est['estacion'].map(nombre_estacion)
        por_est['nombre_linea'] = por_est['linea'].map(nombre_linea)

        if ver == 'Afluencia':
            seccion('Estaciones con más afluencia')
            tabla = por_est.sort_values('afluencia', ascending=False).head(15)
            st.dataframe(tabla[['nombre', 'nombre_linea', 'afluencia']], hide_index=True, height=460,
                         column_config={'nombre': 'Estación', 'nombre_linea': 'Línea',
                                        'afluencia': st.column_config.ProgressColumn(
                                            'Pasajeros al día', format='%,.0f', min_value=0,
                                            max_value=float(por_est['afluencia'].max()))})
            st.markdown('<p class="nota">Afluencia diaria típica (mediana) en el periodo, sin contar días de cierre.</p>',
                        unsafe_allow_html=True)
        else:
            seccion('Estaciones con más anomalías')
            tabla = por_est.sort_values('anomalias', ascending=False).head(15)
            st.dataframe(tabla[['nombre', 'nombre_linea', 'anomalias']], hide_index=True, height=460,
                         column_config={'nombre': 'Estación', 'nombre_linea': 'Línea',
                                        'anomalias': st.column_config.ProgressColumn(
                                            'Anomalías', format='%d', min_value=0,
                                            max_value=float(max(por_est['anomalias'].max(), 1)))})
            st.markdown('<p class="nota">Días del periodo en que la estación se salió de lo normal.</p>',
                        unsafe_allow_html=True)
        st.markdown('<p class="nota">Para ver el detalle de una estación abre <b>Series de tiempo</b>.</p>',
                    unsafe_allow_html=True)

# ---------------------------------------------------------------- series de tiempo
with tab_series:
    lineas = list(dict.fromkeys(estaciones['linea']))
    if st.session_state.get('linea_serie') not in lineas:
        st.session_state['linea_serie'], st.session_state['est_serie'] = 'linea 1', 'pantitlán'
    c1, c2, c3 = st.columns([1, 1.6, 1.6])
    linea_e = c1.selectbox('Línea', lineas, format_func=nombre_linea, key='linea_serie')
    opciones = estaciones.loc[estaciones['linea'] == linea_e, 'estacion'].tolist()
    if st.session_state.get('est_serie') not in opciones:
        st.session_state['est_serie'] = opciones[0]
    est_e = c2.selectbox('Estación', opciones, format_func=nombre_estacion, key='est_serie')
    periodo_s = c3.radio('Mostrar', ['Último año y pronóstico', 'Todo el histórico'], horizontal=True)
    clave = f'{linea_e}|{est_e}'

    s = series[(series['linea'] == linea_e) & (series['estacion'] == est_e)].sort_values('fecha')
    sh, sf = s[~s['es_futuro']], s[s['es_futuro']]
    riesgo = top[(top['linea'] == linea_e) & (top['estacion'] == est_e)]
    graves_anio = sh['prioridad_auditoria'].eq(CRITICA) & (sh['fecha'] > ultimo_dato - pd.Timedelta(days=365))
    c = st.columns(4)
    kpi(c[0], 'Afluencia diaria típica', f'{sh.loc[~sh["prioridad_auditoria"].eq(CIERRE), "afluencia"].median():,.0f}',
        'pasajeros (mediana)')
    kpi(c[1], 'Anomalías graves', f'{sh["prioridad_auditoria"].eq(CRITICA).sum():,}', f'{graves_anio.sum()} en el último año')
    kpi(c[2], 'Esperado próximo mes', f'{sf["yhat"].head(30).mean():,.0f}', 'pasajeros al día (pronóstico)')
    if len(riesgo):
        nivel = 'Alto' if riesgo['riesgo_promedio'].iloc[0] >= 2 else 'Moderado'
        kpi(c[3], 'Riesgo en los próximos meses', nivel, f'{int(riesgo["dias_en_alerta"].iloc[0])} días en alerta')
    else:
        kpi(c[3], 'Riesgo en los próximos meses', 'Normal', 'sin alertas destacadas')

    if periodo_s != 'Todo el histórico':
        sh = sh[sh['fecha'] > ultimo_dato - pd.Timedelta(days=365)]
    graves = sh[sh['prioridad_auditoria'].eq(CRITICA)]
    leves = sh[sh['prioridad_auditoria'].isin(MENORES)]
    cierres = sh[sh['prioridad_auditoria'].eq(CIERRE)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pd.concat([sh['fecha'], sh['fecha'][::-1]]), y=pd.concat([sh['yhat_upper'], sh['yhat_lower'][::-1]]),
                             fill='toself', fillcolor='rgba(95,99,104,0.16)', line=dict(width=0), hoverinfo='skip',
                             name='Rango normal'))
    fig.add_trace(go.Scatter(x=pd.concat([sf['fecha'], sf['fecha'][::-1]]), y=pd.concat([sf['yhat_upper'], sf['yhat_lower'][::-1]]),
                             fill='toself', fillcolor='rgba(242,101,34,0.20)', line=dict(width=0), hoverinfo='skip',
                             name='Rango pronosticado'))
    fig.add_trace(go.Scatter(x=sh['fecha'], y=sh['afluencia'], name='Afluencia real', line=dict(color=GRIS_OSCURO, width=1.3),
                             hovertemplate='%{x|%d/%m/%Y}: %{y:,.0f} pasajeros<extra></extra>'))
    fig.add_trace(go.Scatter(x=sf['fecha'], y=sf['yhat'], name='Pronóstico', line=dict(color=NARANJA, width=2.2),
                             hovertemplate='%{x|%d/%m/%Y}: %{y:,.0f} esperados<extra>Pronóstico</extra>'))
    for datos_p, nombre, color, tam in [(leves, 'Anomalía leve', NARANJA_CLARO, 5), (graves, 'Anomalía grave', ROJO, 8),
                                        (cierres, 'Estación cerrada', '#9E9E9E', 4)]:
        if len(datos_p):
            fig.add_trace(go.Scatter(x=datos_p['fecha'], y=datos_p['afluencia'], mode='markers', name=nombre,
                                     marker=dict(color=color, size=tam, line=dict(color='white', width=.6)),
                                     customdata=datos_p[['yhat']].values,
                                     hovertemplate='%{x|%d/%m/%Y}<br>Real: %{y:,.0f}<br>Esperado: %{customdata[0]:,.0f}'
                                                   '<extra>' + nombre + '</extra>'))
    fig.add_vline(x=ultimo_dato, line_dash='dot', line_color=GRIS)
    fig.add_annotation(x=ultimo_dato, y=1, yref='paper', text='Último dato', showarrow=False, xanchor='right',
                       font=dict(color=GRIS, size=11))
    fig.update_layout(template='plotly_white', height=500, margin=dict(l=10, r=10, t=50, b=10),
                      title=dict(text=etiqueta_estacion[clave], font=dict(size=17, color=GRIS_OSCURO)),
                      font=dict(family=FUENTE, color=GRIS_OSCURO, size=12), hovermode='closest',
                      legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='right', x=1, title=None))
    fig.update_yaxes(tickformat=',', title='Pasajeros por día', rangemode='tozero')
    st.plotly_chart(fig)
    st.markdown('<p class="nota">La franja gris es el rango de afluencia que el modelo considera normal para cada día '
                '(toma en cuenta día de la semana, temporada y festivos). Los puntos rojos son días que se salieron de forma '
                'grave; la línea naranja es lo que se espera en los próximos meses.</p>', unsafe_allow_html=True)

    seccion('Anomalías graves más recientes')
    tabla = (s[s['prioridad_auditoria'].eq(CRITICA)].sort_values('fecha', ascending=False).head(10)
             .merge(bitacora[['fecha', 'linea', 'estacion', 'causa', 'descripcion_incidente']],
                    on=['fecha', 'linea', 'estacion'], how='left'))
    if len(tabla):
        tabla['tipo'] = (tabla['diferencia'] > 0).map({True: 'Más gente de lo normal', False: 'Menos gente de lo normal'})
        tabla['causa'] = tabla['causa'].fillna('Sin investigar')
        st.dataframe(tabla.assign(fecha=tabla['fecha'].dt.date)[['fecha', 'tipo', 'afluencia', 'yhat', 'causa', 'descripcion_incidente']],
                     hide_index=True,
                     column_config={'fecha': 'Fecha', 'tipo': 'Qué pasó',
                                    'afluencia': st.column_config.NumberColumn('Real', format='%,.0f'),
                                    'yhat': st.column_config.NumberColumn('Esperado', format='%,.0f'),
                                    'causa': 'Causa encontrada', 'descripcion_incidente': 'Detalle'})
    else:
        st.info('Esta estación no tiene anomalías graves registradas.')

st.markdown('<p class="nota" style="text-align:center;margin-top:28px">Trabajo Terminal 2026-B125 · Datos abiertos de SEMOVI '
            '(datos.cdmx.gob.mx) · Proyecto académico, no es un sitio oficial del STC Metro.</p>', unsafe_allow_html=True)
