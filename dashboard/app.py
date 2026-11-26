# Dashboard del monitor de anomalias de afluencia del Metro CDMX, pensado para
# usuarios: mapa de la red (lineas con su color y estaciones como burbujas por
# afluencia o anomalias) con el ranking de estaciones, y series de
# tiempo por estacion (real, esperado por Prophet y pronostico). El mapa de
# ArcGIS Online del equipo queda como vista opcional.
# Contexto de los datos: dashboard/ANALISIS.md.
#
# Solo lee archivos que estan en el repo (dashboard/data/*.parquet, que genera
# dashboard/preparar_datos.py), asi que se puede desplegar tal cual en
# Streamlit Community Cloud.
#
# La pestana activa y los filtros viven en la URL (bind='query-params'): si la
# sesion se pierde por inactividad y el navegador reconecta o recarga, la pagina
# vuelve con la misma vista y los mismos filtros. Requiere Streamlit >= 1.67.
#
# Correr con la raiz del repo como working directory:
#   streamlit run dashboard/app.py

import base64
import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
DATOS = BASE / 'data'
LOGO = BASE / 'assets' / 'logo_metro.webp'

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

# Colores de las lineas (identidad del STC) y escalas del mapa: de claro (poco) a intenso (mucho)
COLORES_LINEA = {'linea 1': '#E9468F', 'linea 2': '#0065B3', 'linea 3': '#AF9800', 'linea 4': '#5FB0A6',
                 'linea 5': '#F3C700', 'linea 6': '#D52B1E', 'linea 7': '#E87722', 'linea 8': '#009A44',
                 'linea 9': '#6B3A2A', 'linea a': '#9A1D97', 'linea b': '#6E8B74', 'linea 12': '#B49B57'}
ESCALAS = {'afluencia': [[0, '#FFF1E0'], [0.35, '#F9A66C'], [0.7, NARANJA], [1, '#7A2E0B']],
           'anomalias': [[0, '#FFE3E0'], [0.35, '#F28B82'], [0.7, '#D32F2F'], [1, '#5C0A0A']]}

# Vigia de conexion: Streamlit muestra el elemento stConnectionStatus solo mientras NO hay conexion con
# el servidor. Si lleva asi mas de 45 s con la pestana visible y el servidor si responde, la pagina se
# recarga sola (los filtros se conservan porque estan en la URL). Maximo 3 recargas cada 10 minutos.
VIGIA_CONEXION = """<script>
(function () {
  if (window.__vigiaMetro) return;
  window.__vigiaMetro = true;
  var REVISAR = 5000, ESPERA = 45000, MAX_RECARGAS = 3, VENTANA = 600000;
  var desde = null, ultimo = Date.now();
  function recargasRecientes() {
    try {
      return JSON.parse(sessionStorage.getItem('vigiaMetro') || '[]')
        .filter(function (t) { return Date.now() - t < VENTANA; });
    } catch (e) { return []; }
  }
  setInterval(function () {
    var ahora = Date.now();
    var pausa = ahora - ultimo > 3 * REVISAR;   // la pestana estuvo dormida o en segundo plano
    ultimo = ahora;
    var sinConexion = !!document.querySelector('[data-testid="stConnectionStatus"]');
    if (!sinConexion || document.hidden) { desde = null; return; }
    if (pausa || desde === null) { desde = ahora; return; }   // empieza (o reinicia) la cuenta
    if (ahora - desde < ESPERA) return;
    desde = ahora;
    var previas = recargasRecientes();
    if (previas.length >= MAX_RECARGAS || !navigator.onLine) return;
    fetch('_stcore/health', { cache: 'no-store' }).then(function (r) {
      if (!r.ok) return;
      try { sessionStorage.setItem('vigiaMetro', JSON.stringify(previas.concat(Date.now()))); } catch (e) {}
      location.reload();
    }).catch(function () {});
  }, REVISAR);
})();
</script>"""

st.set_page_config(page_title='Monitor de anomalías · Metro CDMX', layout='wide',
                   page_icon=str(LOGO) if LOGO.exists() else None)

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
.encabezado {{ background: linear-gradient(90deg, {GRIS_OSCURO} 0%, #474747 100%); border-bottom: 6px solid {NARANJA};
  border-radius: 12px; padding: 20px 28px; color: #fff; margin-bottom: 16px; display: flex; align-items: center; gap: 18px; }}
.encabezado .logo {{ min-width: 56px; height: 56px; border-radius: 14px; background: {NARANJA}; display: flex;
  align-items: center; justify-content: center; font-weight: 800; font-size: 30px; color: #fff; }}
.encabezado img.logo {{ width: 60px; min-width: 60px; height: 60px; background: none; border-radius: 0; }}
.encabezado h1 {{ font-size: 1.6rem; margin: 0; padding: 0; color: #fff; font-weight: 700; }}
.encabezado p {{ margin: 3px 0 0 0; color: #D6D6D6; font-size: 0.95rem; }}
.kpi {{ background: #fff; border-radius: 10px; padding: 14px 18px; border-left: 5px solid {NARANJA};
  box-shadow: 0 1px 4px rgba(0,0,0,.08); height: 122px; box-sizing: border-box; overflow: hidden;
  display: flex; flex-direction: column; justify-content: center; }}
.kpi .l {{ font-size: .74rem; color: {GRIS}; text-transform: uppercase; letter-spacing: .05em; line-height: 1.25; }}
.kpi .v {{ font-size: 1.6rem; font-weight: 700; color: {GRIS_OSCURO}; line-height: 1.3; }}
.kpi .s {{ font-size: .8rem; color: {NARANJA}; line-height: 1.3; }}
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


@st.cache_resource(show_spinner='Cargando datos…')
def cargar():
    # cache_resource: una sola copia en memoria compartida por todas las sesiones (no se modifica)
    series = pd.read_parquet(DATOS / 'series_estaciones.parquet')
    for col in ['linea', 'estacion']:
        series[col] = series[col].astype(str)
    series['prioridad_auditoria'] = series['prioridad_auditoria'].astype(object)
    series['diferencia'] = series['afluencia'] - series['yhat']
    top = pd.read_parquet(DATOS / 'riesgo_top_estaciones.parquet')
    # Bitacora OSINT de los dias pronosticados (ago-nov 2026) que ya se investigaron
    auditadas = pd.read_csv(DATOS / 'anomalias_auditadas.csv')
    auditadas['fecha'] = pd.to_datetime(auditadas['fecha']).dt.normalize()
    auditadas['causa'] = auditadas['hallazgo_principal'].str.split('(').str[0].str.strip()
    auditadas['ocurrio'] = auditadas['ocurrio_evento'].str.split(' - ').str[0]
    auditadas['tipo'] = auditadas['direccion_probable'].map(
        {'Alza (Pico atípico)': 'Más gente de lo normal', 'Baja (Caída atípica)': 'Menos gente de lo normal'}).fillna('Sin definir')
    auditadas['grupo'] = auditadas['estrato'].map(
        {'A - Alta': 'Riesgo alto', 'B - Media': 'Riesgo medio', 'C - Control': 'Control (riesgo bajo)'})
    coords = pd.read_csv(BASE / 'estaciones_coordenadas.csv')
    return series, top, auditadas, coords


def ordenar_estaciones(puntos):
    # El dataset no trae la geometria de las lineas: se trazan uniendo sus estaciones en orden. El orden es
    # el camino mas corto entre los dos extremos (vecino mas cercano desde el extremo y luego mejora 2-opt),
    # que para las 12 lineas reproduce el recorrido real.
    def dist(a, b):
        return math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(19.4)))

    n = len(puntos)
    if n < 3:
        return list(range(n))
    camino = [max(range(n), key=lambda i: max(dist(puntos[i], q) for q in puntos))]
    libres = set(range(n)) - set(camino)
    while libres:
        j = min(libres, key=lambda k: dist(puntos[camino[-1]], puntos[k]))
        camino.append(j)
        libres.remove(j)
    mejora = True
    while mejora:
        mejora = False
        for a in range(n - 2):
            for b in range(a + 2, n):
                cola = b + 1 < n
                antes = dist(puntos[camino[a]], puntos[camino[a + 1]]) + (dist(puntos[camino[b]], puntos[camino[b + 1]]) if cola else 0)
                despues = dist(puntos[camino[a]], puntos[camino[b]]) + (dist(puntos[camino[a + 1]], puntos[camino[b + 1]]) if cola else 0)
                if despues < antes - 1e-12:
                    camino[a + 1:b + 1] = camino[a + 1:b + 1][::-1]
                    mejora = True
    return camino


@st.cache_resource(show_spinner=False)
def trazos_lineas(coords):
    trazos = {}
    for linea, g in coords.drop_duplicates(['linea', 'lat', 'lon']).groupby('linea'):
        g = g.reset_index(drop=True)
        orden = ordenar_estaciones(list(zip(g['lat'], g['lon'])))
        trazos[linea] = (g.loc[orden, 'lat'].tolist(), g.loc[orden, 'lon'].tolist())
    return trazos


def mapa_red(por_est, columna, titulo, formato, linea_sel, est_sel):
    d = por_est.merge(coords, on=['linea', 'estacion'], how='inner')
    valor = d[columna].astype(float)
    vmax = max(valor.max(), 1)
    # Raiz cuadrada: el AREA de la burbuja es proporcional al valor; las grandes se dibujan primero
    d = d.assign(valor=valor, tam=7 + 33 * (valor / vmax) ** 0.5,
                 texto=valor.map(lambda v: f'{v:,.0f}')).sort_values('valor', ascending=False)
    # Con una linea elegida, el resto de la red se atenua y la vista se acerca a esa linea o estacion
    enfoque = linea_sel != TODA_RED
    activa = d['linea'].eq(linea_sel) | (not enfoque)
    centro, zoom = dict(lat=19.41, lon=-99.125), 10.4
    elegida = d[d['linea'].eq(linea_sel) & d['estacion'].eq(est_sel)]
    if len(elegida):
        centro, zoom = dict(lat=elegida['lat'].iloc[0], lon=elegida['lon'].iloc[0]), 12.6
    elif enfoque and linea_sel in trazos:
        lat, lon = trazos[linea_sel]
        centro, zoom = dict(lat=sum(lat) / len(lat), lon=sum(lon) / len(lon)), 11.2

    fig = go.Figure()
    for linea in sorted(trazos, key=lambda l: (len(l.split()[-1]), l.split()[-1])):
        lat, lon = trazos[linea]
        es_activa = not enfoque or linea == linea_sel
        fig.add_trace(go.Scattermap(lat=lat, lon=lon, mode='lines', name=nombre_linea(linea), hoverinfo='skip',
                                    opacity=1 if es_activa else 0.25,
                                    line=dict(color=COLORES_LINEA.get(linea, GRIS), width=8 if enfoque and es_activa else 5)))
    # Estacion elegida: anillo oscuro grande debajo de su burbuja
    if len(elegida):
        fig.add_trace(go.Scattermap(lat=elegida['lat'], lon=elegida['lon'], mode='markers', hoverinfo='skip',
                                    showlegend=False, marker=dict(size=elegida['tam'] + 18, color=GRIS_OSCURO)))
    # Halo blanco debajo de cada burbuja para que se distinga sobre las lineas
    fig.add_trace(go.Scattermap(lat=d['lat'], lon=d['lon'], mode='markers', hoverinfo='skip', showlegend=False,
                                marker=dict(size=d['tam'] + 4, color='white', opacity=activa.map({True: 0.95, False: 0.3}))))
    fig.add_trace(go.Scattermap(
        lat=d['lat'], lon=d['lon'], mode='markers', showlegend=False, name=titulo,
        marker=dict(size=d['tam'], color=d['valor'], colorscale=ESCALAS[columna], cmin=0, cmax=vmax,
                    opacity=activa.map({True: 0.92, False: 0.25}),
                    colorbar=dict(title=dict(text=titulo, side='top'), thickness=14, len=0.45, x=0.99, xanchor='right',
                                  y=0.02, yanchor='bottom', tickformat=formato, bgcolor='rgba(255,255,255,0.85)')),
        customdata=d[['estacion', 'linea', 'texto']].assign(estacion=d['estacion'].map(nombre_estacion),
                                                            linea=d['linea'].map(nombre_linea)).values,
        hovertemplate='<b>%{customdata[0]}</b> · %{customdata[1]}<br>' + titulo + ': %{customdata[2]}<extra></extra>'))
    if len(elegida):
        fig.add_trace(go.Scattermap(lat=elegida['lat'], lon=elegida['lon'], mode='text', hoverinfo='skip',
                                    showlegend=False, text=[nombre_estacion(est_sel)], textposition='top right',
                                    textfont=dict(size=16, color=GRIS_OSCURO)))
    # uirevision: el zoom que haga el usuario se respeta hasta que cambie la seleccion
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0), font=dict(family=FUENTE, color=GRIS_OSCURO),
                      uirevision=f'{linea_sel}|{est_sel}',
                      map=dict(style='carto-positron', center=centro, zoom=zoom),
                      legend=dict(title=dict(text='Líneas'), x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.88)',
                                  bordercolor=GRIS_CLARO, borderwidth=1, font=dict(size=12)))
    st.plotly_chart(fig, config={'displaylogo': False, 'scrollZoom': True})


def config_arcgis(clave, valor):
    # Constante del codigo primero; si esta vacia, Secrets de Streamlit (si existen)
    if valor:
        return valor
    try:
        return st.secrets.get(clave, '')
    except Exception:
        return ''


faltan = [p for p in [DATOS / 'series_estaciones.parquet', DATOS / 'riesgo_top_estaciones.parquet',
                      DATOS / 'anomalias_auditadas.csv', BASE / 'estaciones_coordenadas.csv'] if not p.exists()]
if faltan:
    st.error('Faltan datos del dashboard: ' + ', '.join(str(p.relative_to(REPO)) for p in faltan) +
             '. Corre `python dashboard/preparar_datos.py` desde la raíz del repo.')
    st.stop()

series, top, auditadas, coords = cargar()
trazos = trazos_lineas(coords)
hist = series[~series['es_futuro']]
futuro = series[series['es_futuro']]
ultimo_dato = hist['fecha'].max()
arcgis_url = config_arcgis('arcgis_url', ARCGIS_URL)

estaciones = (hist[['linea', 'estacion']].drop_duplicates()
              .assign(clave=lambda d: d['linea'] + '|' + d['estacion'],
                      orden=lambda d: d['linea'].str.split().str[-1].map(lambda x: (len(x), x)))
              .sort_values(['orden', 'estacion']))
etiqueta_estacion = {r.clave: f'{nombre_estacion(r.estacion)} · {nombre_linea(r.linea)}' for r in estaciones.itertuples()}

# Logo del Metro incrustado en base64 (el HTML de st.markdown no puede leer archivos locales); sin el archivo, una M
logo_html = (f'<img class="logo" alt="Logo del Metro CDMX" src="data:image/webp;base64,'
             f'{base64.b64encode(LOGO.read_bytes()).decode()}">' if LOGO.exists() else '<div class="logo">M</div>')
st.markdown(f"""
<div class="encabezado">{logo_html}<div>
<h1>Monitor de anomalías de afluencia · Metro CDMX</h1>
<p>Afluencia · Anomalías · Pronóstico</p></div></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- filtros de linea/estacion + indicadores
# Linea y estacion se eligen arriba y valen para toda la pagina: indicadores, mapa, ranking y serie de tiempo.
# Se guardan en la URL a mano (sin bind): asi abrir_estacion() puede fijarlas desde el ranking sin que un valor
# viejo de la URL las sobrescriba al volver a mostrarse.
TODA_RED, TODAS = 'red', 'todas'
lineas = list(dict.fromkeys(estaciones['linea']))
url = st.query_params
c = st.columns([1.5, 1, 1, 1, 1])
with c[0]:
    opciones_l = [TODA_RED] + lineas
    if st.session_state.get('linea') not in opciones_l:
        st.session_state['linea'] = url.get('linea') if url.get('linea') in opciones_l else TODA_RED
    linea_sel = st.selectbox('Línea', opciones_l, key='linea',
                             format_func=lambda l: 'Toda la red' if l == TODA_RED else nombre_linea(l))
    opciones_e = [TODAS] + ([] if linea_sel == TODA_RED
                            else estaciones.loc[estaciones['linea'] == linea_sel, 'estacion'].tolist())
    if st.session_state.get('estacion') not in opciones_e:   # primera vez o cambio de linea
        st.session_state['estacion'] = url.get('estacion') if url.get('estacion') in opciones_e else TODAS
    est_sel = st.selectbox('Estación', opciones_e, key='estacion', disabled=linea_sel == TODA_RED,
                           format_func=lambda e: 'Todas las estaciones' if e == TODAS else nombre_estacion(e))
url['linea'], url['estacion'] = linea_sel, est_sel


def filtrar(df):
    if linea_sel != TODA_RED:
        df = df[df['linea'] == linea_sel]
    if est_sel != TODAS:
        df = df[df['estacion'] == est_sel]
    return df


# Indicadores de la seleccion (toda la red, una linea o una estacion), con todo el historico disponible
sel_hist = filtrar(hist)
pasajeros_dia = sel_hist[~sel_hist['prioridad_auditoria'].eq(CIERRE)].groupby('fecha')['afluencia'].sum().mean()
anios = (ultimo_dato - hist['fecha'].min()).days / 365.25
graves_total = int(sel_hist['prioridad_auditoria'].eq(CRITICA).sum())
graves_anio = graves_total / anios
# Solo los 30 dias despues del ultimo dato (estaciones que dejaron de reportar antes tienen "futuro" mas temprano)
proximo_mes = futuro[(futuro['fecha'] > ultimo_dato) & (futuro['fecha'] <= ultimo_dato + pd.Timedelta(days=30))]
esperado = filtrar(proximo_mes).groupby('fecha')['yhat'].sum().mean()
riesgo_sel = filtrar(top)
# Real (SEMOVI) contra pronostico (Prophet): el cambio dice si se espera mas o menos gente que de costumbre
cambio = esperado / pasajeros_dia - 1
kpi(c[1], 'Pasajeros al día · real', f'{pasajeros_dia:,.0f}', f'promedio {hist["fecha"].min():%m/%Y} a {ultimo_dato:%m/%Y}')
kpi(c[2], 'Anomalías graves al año', f'{graves_anio:,.1f}' if graves_anio < 10 else f'{graves_anio:,.0f}',
    f'{graves_total:,} en total desde {hist["fecha"].min().year}')
kpi(c[3], 'Pasajeros al día · pronóstico', f'{esperado:,.0f}', f'próximo mes · {cambio:+.0%} vs. real')
if est_sel != TODAS:
    if len(riesgo_sel):
        nivel = 'Alto' if riesgo_sel['riesgo_promedio'].iloc[0] >= 2 else 'Moderado'
        kpi(c[4], 'Riesgo próximos meses', nivel, f'{int(riesgo_sel["dias_en_alerta"].iloc[0])} días en alerta')
    else:
        kpi(c[4], 'Riesgo próximos meses', 'Normal', 'sin alertas destacadas')
else:
    kpi(c[4], 'Estaciones en alerta', f'{len(riesgo_sel)}', f'{int(riesgo_sel["dias_en_alerta"].sum()):,} días en alerta')
st.write('')


def abrir_estacion():
    # Al marcar una fila del ranking se abre la serie de tiempo de esa estacion
    filas = st.session_state['ranking']['selection']['rows']
    if filas:
        st.session_state['linea'], st.session_state['estacion'] = st.session_state['ranking_estaciones'][filas[0]]
        st.session_state['vista'] = 'Series de tiempo'


# ---------------------------------------------------------------- mapa de la red + ranking de estaciones
def vista_mapa():
    izq, der = st.columns([2.5, 1])
    with der:
        ver = st.radio('Ver', ['Afluencia', 'Anomalías'], horizontal=True, key='ver', bind='query-params')
        periodo = st.selectbox('Periodo', list(PERIODOS), key='periodo', bind='query-params')
        menores = ver == 'Anomalías' and st.toggle(
            'Incluir anomalías leves', value=False, key='leves', bind='query-params',
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
            columna, titulo, encabezado, formato = 'afluencia', 'Estaciones con más afluencia', 'Pasajeros al día', '%,.0f'
            nota = 'Afluencia diaria típica (mediana) en el periodo, sin contar días de cierre.'
            leyenda_mapa = ('Cada círculo es una estación: entre más grande y más intenso, más pasajeros al día '
                            '(mediana del periodo, sin días de cierre).')
        else:
            columna, titulo, encabezado, formato = 'anomalias', 'Estaciones con más anomalías', 'Anomalías', '%d'
            nota = 'Días del periodo en que la estación se salió de lo normal.'
            leyenda_mapa = ('Cada círculo es una estación: entre más grande y más rojo, más días se salió de lo normal '
                            'en el periodo.')
        if linea_sel != TODA_RED:
            titulo += ' · ' + nombre_linea(linea_sel)
        seccion(titulo)
        tabla = por_est[por_est['linea'].eq(linea_sel) | (linea_sel == TODA_RED)].sort_values(columna, ascending=False).head(15)
        st.session_state['ranking_estaciones'] = list(zip(tabla['linea'], tabla['estacion']))
        st.dataframe(tabla[['nombre', 'nombre_linea', columna]], hide_index=True, height=460,
                     key='ranking', on_select=abrir_estacion, selection_mode='single-row',
                     column_config={'nombre': 'Estación', 'nombre_linea': 'Línea',
                                    columna: st.column_config.ProgressColumn(
                                        encabezado, format=formato, min_value=0,
                                        max_value=float(max(tabla[columna].max(), 1)))})
        st.markdown(f'<p class="nota">{nota}</p><p class="nota">Marca la casilla de una estación para abrir su '
                    '<b>serie de tiempo</b>.</p>', unsafe_allow_html=True)

    with izq:
        mapa_red(por_est, columna, encabezado, ',.0f', linea_sel, est_sel)
        st.markdown(f'<p class="nota">{leyenda_mapa} La línea o estación elegida en los filtros de arriba se resalta. '
                    'Las estaciones de correspondencia tienen un círculo por línea. '
                    'Acerca con la rueda del ratón y pasa el cursor sobre una estación para ver su valor.</p>',
                    unsafe_allow_html=True)
        if arcgis_url:
            with st.expander('Ver también el mapa de ArcGIS Online del equipo'):
                st.iframe(arcgis_url, height=560)
                st.markdown(f'<p class="nota">Si no carga, ábrelo directamente: <a href="{arcgis_url}" target="_blank">'
                            'ver en ArcGIS Online</a>.</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------- series de tiempo
def vista_series():
    # Linea y estacion vienen de los filtros de arriba; los indicadores de la estacion tambien estan arriba
    if est_sel == TODAS:
        st.info('Elige una línea y una estación en los filtros de arriba para ver su serie de tiempo.')
        return
    linea_e, est_e = linea_sel, est_sel
    periodo_s = st.radio('Mostrar', ['Último año y pronóstico', 'Todo el histórico'], horizontal=True,
                         key='mostrar', bind='query-params')
    clave = f'{linea_e}|{est_e}'

    s = series[(series['linea'] == linea_e) & (series['estacion'] == est_e)].sort_values('fecha')
    sh, sf = s[~s['es_futuro']], s[s['es_futuro']]

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
    st.plotly_chart(fig, config={'displaylogo': False,
                                 'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'zoomIn2d', 'zoomOut2d']})
    st.markdown('<p class="nota">La franja gris es el rango de afluencia que el modelo considera normal para cada día '
                '(toma en cuenta día de la semana, temporada y festivos). Los puntos rojos son días que se salieron de forma '
                'grave; la línea naranja es lo que se espera en los próximos meses. Arrastra sobre la gráfica para acercarte '
                'a un periodo y haz doble clic para regresar.</p>', unsafe_allow_html=True)

    seccion('Últimas anomalías auditadas')
    todas = st.toggle('Ver todas las estaciones', value=False, key='todas_auditadas', bind='query-params')
    tabla = auditadas if todas else auditadas[(auditadas['linea'] == linea_e) & (auditadas['estacion'] == est_e)]
    if len(tabla):
        tabla = tabla.sort_values('fecha', ascending=False).assign(
            fecha=lambda d: d['fecha'].dt.date, nombre=lambda d: d['estacion'].map(nombre_estacion),
            nombre_linea=lambda d: d['linea'].map(nombre_linea))
        columnas = (['nombre', 'nombre_linea'] if todas else []) + [
            'fecha', 'grupo', 'prob_critica', 'ocurrio', 'tipo', 'afluencia_esperada', 'afluencia_real_semovi',
            'causa', 'descripcion_incidente', 'link_fuente_1']
        st.dataframe(tabla[columnas], hide_index=True,
                     column_config={'nombre': 'Estación', 'nombre_linea': 'Línea', 'fecha': 'Fecha',
                                    'grupo': 'Grupo de la muestra',
                                    'prob_critica': st.column_config.NumberColumn('Prob. de anomalía grave', format='percent'),
                                    'ocurrio': '¿Ocurrió algo?', 'tipo': 'Qué pasó',
                                    'afluencia_esperada': st.column_config.NumberColumn('Esperado', format='%,.0f'),
                                    'afluencia_real_semovi': st.column_config.NumberColumn('Real', format='%,.0f'),
                                    'causa': 'Causa encontrada', 'descripcion_incidente': 'Detalle',
                                    'link_fuente_1': st.column_config.LinkColumn('Fuente', display_text='Ver nota')})
    else:
        st.info('Esta estación no está en la muestra auditada. Activa "Ver todas las estaciones" para ver las demás.')
    st.markdown(f'<p class="nota">Días de agosto a noviembre de 2026 que el modelo de riesgo marcó como posibles anomalías '
                f'y que se investigaron en noticias y redes (OSINT): {len(auditadas)} días en '
                f'{auditadas[["linea", "estacion"]].drop_duplicates().shape[0]} estaciones. Los días de "Control" se investigaron '
                'igual que los demás para comparar contra los que marcó el modelo.</p>', unsafe_allow_html=True)

# Solo se calcula la pestana abierta; la pestana activa queda en la URL
tab_mapa, tab_series = st.tabs(['Mapa', 'Series de tiempo'], key='vista', bind='query-params')
if tab_mapa.open:
    with tab_mapa:
        vista_mapa()
if tab_series.open:
    with tab_series:
        vista_series()

st.markdown('<p class="nota" style="text-align:center;margin-top:28px">Trabajo Terminal 2026-B125 · Datos abiertos de SEMOVI '
            '(datos.cdmx.gob.mx) · Proyecto académico, no es un sitio oficial del STC Metro.</p>', unsafe_allow_html=True)
st.html(VIGIA_CONEXION, unsafe_allow_javascript=True)
