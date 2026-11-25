# %% [markdown]
# Estaciones y lineas mas conflictivas, sus causas y el efecto de cada causa en la afluencia.
# Usa dos fuentes que ya estan en el repo:
# - master_auditoria_consenso_MAD.csv: todas las anomalias del detector (Prophet + MAD), 2022 a jul-2026.
#   De aqui sale CUANTO y DONDE (anomalias CRITICAS y pasajeros afectados).
# - bitacora_investigacion_anomalias_criticas.csv: OSINT manual de 371 anomalias criticas
#   (muestra estratificada por linea y direccion). De aqui sale POR QUE y CUANTO MUEVE cada causa.
# Ejecutar desde la raiz del repo:  python estaciones_y_causas/estaciones_y_causas.py
# Lectura de resultados y limites: estaciones_y_causas/ANALISIS.md

# %%
import os
import sys
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, os.getcwd())   # historial.py vive en la raiz del repo
from historial import registrar_corrida
sys.path.insert(0, os.path.join(os.getcwd(), 'validacion_predicciones'))
from bitacora_prediccion import leer_bitacora_pred   # OSINT de los dias en alerta 2026 (original + ajuste del 16-sep)

CARPETA = 'estaciones_y_causas'
IMG = f'{CARPETA}/img'
RES = f'{CARPETA}/resultados'
os.makedirs(IMG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

MASTER = 'master_auditoria_consenso_MAD.csv'
BITACORA = 'bitacora_investigacion_anomalias_criticas.csv'
TOP_ESTACIONES = 15
RUIDO = 'Falsa Alarma'   # causa que sirve de referencia: desviaciones sin evento identificado


def nombre_linea(linea):
    return linea.replace('linea', 'Línea').replace(' a', ' A').replace(' b', ' B')


def nombre_estacion(estacion):
    palabras = (p if p in ('de', 'del', 'la', 'las', 'los', 'y') else p.capitalize() for p in estacion.split(' '))
    return '/'.join(t[:1].upper() + t[1:] for t in ' '.join(palabras).split('/'))


# %% [markdown]
# ## 1. Anomalias CRITICAS del detector: lineas y estaciones
# Pasajeros afectados = suma de |afluencia real - afluencia esperada por Prophet| en los dias CRITICOS.
# Se reporta por estacion para no castigar a las lineas con mas estaciones.

# %%
master = pd.read_csv(MASTER)
criticas = master[master['prioridad_auditoria'].str.startswith('CRÍTICA')].copy()
criticas['caida'] = criticas['impacto_pasajeros'] < 0
criticas['pasajeros_afectados'] = criticas['impacto_pasajeros'].abs()
criticas['cambio_pct'] = criticas['impacto_pasajeros'] / criticas['yhat'] * 100

lineas = criticas.groupby('linea').agg(
    estaciones=('estacion', 'nunique'),
    dias_criticos=('fecha', 'size'),
    pct_caidas=('caida', 'mean'),
    pasajeros_afectados=('pasajeros_afectados', 'sum'),
)
lineas['dias_criticos_por_estacion'] = lineas['dias_criticos'] / lineas['estaciones']
lineas['pasajeros_afectados_por_estacion'] = lineas['pasajeros_afectados'] / lineas['estaciones']
lineas['pct_caidas'] *= 100
lineas = lineas.sort_values('pasajeros_afectados_por_estacion', ascending=False)

estaciones = criticas.groupby(['linea', 'estacion']).agg(
    dias_criticos=('fecha', 'size'),
    pct_caidas=('caida', 'mean'),
    pasajeros_afectados=('pasajeros_afectados', 'sum'),
    pasajeros_en_caidas=('impacto_pasajeros', lambda s: -s[s < 0].sum()),
    pasajeros_en_alzas=('impacto_pasajeros', lambda s: s[s > 0].sum()),
    cambio_tipico_pct=('cambio_pct', lambda s: s.abs().median()),
)
estaciones['pct_caidas'] *= 100
estaciones = estaciones.sort_values('pasajeros_afectados', ascending=False)

# %% [markdown]
# ## 2. Causas documentadas por la OSINT (por linea y por estacion)
# La muestra OSINT es proporcional por linea, asi que el reparto de causas dentro de cada linea
# es comparable entre lineas. Por estacion hay de 0 a 7 registros: solo se reporta lo documentado.

# %%
osint = pd.read_csv(BITACORA)
osint.columns = osint.columns.str.lower()
osint['causa'] = osint['hallazgo_principal'].str.strip().str.split(' (', regex=False).str[0]
ORDEN_CAUSAS = osint['causa'].value_counts().index.tolist()

causas_linea = pd.crosstab(osint['linea'], osint['causa']).reindex(columns=ORDEN_CAUSAS, fill_value=0)
causas_linea_pct = causas_linea.div(causas_linea.sum(axis=1), axis=0) * 100
con_evento = causas_linea.drop(columns=RUIDO)
lineas['registros_osint'] = causas_linea.sum(axis=1)
lineas['pct_falsa_alarma_osint'] = causas_linea_pct[RUIDO]
lineas['causa_principal_osint'] = con_evento.idxmax(axis=1)
lineas['causa_principal_pct'] = con_evento.max(axis=1) / causas_linea.sum(axis=1) * 100
lineas['segunda_causa_osint'] = con_evento.apply(lambda f: f.sort_values(ascending=False).index[1], axis=1)

def causas_documentadas(grupo):
    vc = grupo['causa'].value_counts()
    return '; '.join(f'{c} ({n})' for c, n in vc.items())

doc = osint.groupby(['linea', 'estacion']).apply(causas_documentadas, include_groups=False).rename('causas_osint')
estaciones = estaciones.join(doc)
estaciones['registros_osint'] = osint.groupby(['linea', 'estacion']).size().reindex(estaciones.index).fillna(0).astype(int)

lineas.round(1).to_csv(f'{RES}/lineas_conflictivas.csv', encoding='utf-8-sig')
estaciones.round(1).to_csv(f'{RES}/estaciones_conflictivas.csv', encoding='utf-8-sig')
causas_linea.assign(total=causas_linea.sum(axis=1)).to_csv(f'{RES}/causas_por_linea_osint.csv', encoding='utf-8-sig')
print(lineas[['estaciones', 'dias_criticos', 'dias_criticos_por_estacion', 'pasajeros_afectados_por_estacion',
              'pct_caidas', 'causa_principal_osint', 'pct_falsa_alarma_osint']].round(0).to_string())
print(estaciones.head(TOP_ESTACIONES)[['dias_criticos', 'pasajeros_afectados', 'pct_caidas', 'causas_osint']].round(0).to_string())

# %% [markdown]
# ## 3. Efecto de cada causa en la afluencia
# Para cada registro OSINT: cambio % = (afluencia real - esperada) / esperada, con la esperada de
# la version del detector con que se hizo la investigacion (afluencia - impacto_pasajeros).
# Se separan caidas y alzas porque una misma causa puede mover la afluencia en los dos sentidos.
# Se descartan 4 registros cuya afluencia esperada era <= 0 (version sin recorte a cero).

# %%
efecto = osint[osint['afluencia'] - osint['impacto_pasajeros'] > 0].copy()
efecto['esperada'] = efecto['afluencia'] - efecto['impacto_pasajeros']
efecto['cambio_pct'] = efecto['impacto_pasajeros'] / efecto['esperada'] * 100
efecto['sentido'] = np.where(efecto['impacto_pasajeros'] < 0, 'caida', 'alza')

def resumen(d):
    ca, al = d[d['sentido'] == 'caida'], d[d['sentido'] == 'alza']
    return pd.Series({
        'registros': len(d),
        'pct_caidas': len(ca) / len(d) * 100,
        'caidas': len(ca),
        'cambio_mediano_en_caidas_pct': ca['cambio_pct'].median(),
        'pasajeros_medianos_en_caidas': -ca['impacto_pasajeros'].median() if len(ca) else np.nan,
        'alzas': len(al),
        'cambio_mediano_en_alzas_pct': al['cambio_pct'].median(),
        'pasajeros_medianos_en_alzas': al['impacto_pasajeros'].median() if len(al) else np.nan,
    })

efecto_causa = efecto.groupby('causa')[['impacto_pasajeros', 'cambio_pct', 'sentido']].apply(resumen)
efecto_causa = efecto_causa.sort_values('pct_caidas', ascending=False)
efecto_causa.round(1).to_csv(f'{RES}/efecto_por_causa.csv', encoding='utf-8-sig')
print(efecto_causa.round(0).to_string())

# %% [markdown]
# ## 3b. Causas ciclicas, programadas y esporadicas
# Ciclica: se repite con el calendario (feriados y vacaciones, temporada de lluvias, temporada de
# contingencias). Programada: no es ciclica pero se anuncia antes (eventos masivos, cierres programados,
# jornadas electorales). Esporadica: no se puede anticipar con el calendario (fallas, incidentes,
# sustitucion por fallas en otro medio). Las dos primeras se pueden prevenir; la tercera pide deteccion
# y respuesta rapida.
# Evidencia de ciclicidad en el detector: un dia CRITICO es "recurrente" si la misma estacion tuvo otro
# dia CRITICO en la misma fecha (mes-dia) en otro ano. Las fechas moviles (Semana Santa) no se cuentan,
# asi que es un piso.

# %%
TIPO_CAUSA = {
    'Feriado No Oficial / Cultural': 'Cíclica', 'Clima Extremo': 'Cíclica', 'Contingencia Ambiental': 'Cíclica',
    'Evento Masivo': 'Programada', 'Cierre Programado': 'Programada', 'Evento Cívico / Jornada Electoral': 'Programada',
    'Falla Oculta': 'Esporádica', 'Falla Mecánica': 'Esporádica', 'Falla Técnica / Eléctrica': 'Esporádica',
    'Incidente Externo': 'Esporádica', 'Efecto Sustitución': 'Esporádica',
    RUIDO: 'Falsa alarma',
}
TIPOS = ['Cíclica', 'Programada', 'Esporádica', 'Falsa alarma']
osint['tipo_causa'] = osint['causa'].map(TIPO_CAUSA)
osint['mes'] = pd.to_datetime(osint['fecha']).dt.month
tipo_causa = osint.groupby(['tipo_causa', 'causa']).agg(
    registros=('mes', 'size'),
    meses_mas_frecuentes=('mes', lambda m: ', '.join(str(x) for x in m.value_counts().nlargest(3).index)),
    pct_en_3_meses=('mes', lambda m: m.value_counts(normalize=True).nlargest(3).sum() * 100),
).reset_index()
tipo_causa['pct_de_registros'] = tipo_causa['registros'] / len(osint) * 100
tipo_causa.round(1).to_csv(f'{RES}/causas_ciclicas_programadas_esporadicas.csv', index=False, encoding='utf-8-sig')
tipo_linea = pd.crosstab(osint['linea'], osint['tipo_causa']).reindex(columns=TIPOS, fill_value=0)
tipo_linea.loc['Toda la red'] = tipo_linea.sum()
pred = leer_bitacora_pred()
pred_tipo = pred['Hallazgo_Principal'].str.strip().str.split(' (', regex=False).str[0].map(TIPO_CAUSA)
tipo_linea.loc['Alertas de la predicción 2026'] = pred_tipo.value_counts().reindex(TIPOS, fill_value=0)
tipo_linea_pct = tipo_linea.div(tipo_linea.sum(axis=1), axis=0) * 100
tipo_linea.assign(total=tipo_linea.sum(axis=1)).to_csv(f'{RES}/tipo_de_causa_por_linea.csv', encoding='utf-8-sig')
print(tipo_linea_pct.round(0).to_string())

criticas['fecha_dt'] = pd.to_datetime(criticas['fecha'])
criticas['mes_dia'] = criticas['fecha_dt'].dt.strftime('%m-%d')
anios = criticas.groupby(['estacion', 'mes_dia'])['fecha_dt'].transform(lambda f: f.dt.year.nunique())
criticas['recurrente'] = anios >= 2
estaciones['pct_dias_recurrentes'] = criticas.groupby(['linea', 'estacion'])['recurrente'].mean().reindex(estaciones.index) * 100
lineas['pct_dias_recurrentes'] = criticas.groupby('linea')['recurrente'].mean().reindex(lineas.index) * 100
fechas = criticas.groupby('mes_dia').agg(dias_criticos=('estacion', 'size'), dias_recurrentes=('recurrente', 'sum'),
                                         anios=('fecha_dt', lambda f: f.dt.year.nunique()), estaciones=('estacion', 'nunique'))
fechas = fechas.sort_values('dias_recurrentes', ascending=False)   # una fecha unica (p. ej. 11-jun-2026) no cuenta como recurrente
fechas.head(30).to_csv(f'{RES}/fechas_recurrentes.csv', encoding='utf-8-sig')
lineas.round(1).to_csv(f'{RES}/lineas_conflictivas.csv', encoding='utf-8-sig')
estaciones.round(1).to_csv(f'{RES}/estaciones_conflictivas.csv', encoding='utf-8-sig')
print(f"Dias criticos recurrentes (misma estacion y fecha en 2+ anos): {criticas['recurrente'].mean() * 100:.0f}%")
print(fechas.head(12).to_string())

# %% [markdown]
# ## 4. Graficas

# %%
TINTA, TINTA2, FONDO, REJILLA = '#0b0b0b', '#52514e', '#fcfcfb', '#e4e3df'
AZUL, NARANJA, GRIS = '#2a78d6', '#eb6834', '#b9b8b2'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': FONDO, 'axes.facecolor': FONDO,
                     'text.color': TINTA, 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA,
                     'axes.edgecolor': REJILLA})

# Colores de cada linea del Metro (nombres oficiales del STC; hex aproximados). La Linea B es verde y gris.
COLOR_LINEA = {
    'linea 1': '#E9468F',   # rosa mexicano
    'linea 2': '#005EB8',   # azul
    'linea 3': '#AF9800',   # verde olivo
    'linea 4': '#6FBAB3',   # verde agua
    'linea 5': '#FFD100',   # amarillo
    'linea 6': '#DA291C',   # rojo
    'linea 7': '#E87722',   # naranja
    'linea 8': '#009A44',   # verde
    'linea 9': '#6B3A25',   # cafe
    'linea a': '#981D97',   # morado
    'linea b': '#009A44',   # verde (con gris)
    'linea 12': '#B99E51',  # dorado
}
GRIS_LINEA_B = '#A7A8AA'

def barra_linea(ax, y, ancho, linea, alto=0.6, izquierda=0):
    # Barra horizontal con el color de la linea; la Linea B se dibuja mitad verde, mitad gris.
    if linea == 'linea b':
        ax.barh(y + alto / 4, ancho, height=alto / 2, left=izquierda, color=COLOR_LINEA[linea])
        ax.barh(y - alto / 4, ancho, height=alto / 2, left=izquierda, color=GRIS_LINEA_B)
    else:
        ax.barh(y, ancho, height=alto, left=izquierda, color=COLOR_LINEA[linea])

def marcas_linea(ax, posiciones, lineas_fila, x=-0.008, ancho=0.012, alto=0.62):
    # Cuadro de color de la linea junto a cada etiqueta del eje y.
    from matplotlib.patches import Rectangle
    tr = ax.get_yaxis_transform()
    for yi, linea in zip(posiciones, lineas_fila):
        if linea not in COLOR_LINEA:
            continue
        if linea == 'linea b':
            arriba, abajo = (yi - alto / 2, yi) if ax.yaxis_inverted() else (yi, yi - alto / 2)   # verde arriba
            ax.add_patch(Rectangle((x - ancho, arriba), ancho, alto / 2, transform=tr, color=COLOR_LINEA[linea], clip_on=False))
            ax.add_patch(Rectangle((x - ancho, abajo), ancho, alto / 2, transform=tr, color=GRIS_LINEA_B, clip_on=False))
        else:
            ax.add_patch(Rectangle((x - ancho, yi - alto / 2), ancho, alto, transform=tr, color=COLOR_LINEA[linea], clip_on=False))
    ax.tick_params(axis='y', pad=22)

def limpiar_ejes(ax, ejes=('top', 'right', 'left')):
    for s in ejes:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)

DEF_CRITICO = 'Día crítico: Prophet y MAD coinciden en que la afluencia de la estación fue atípica (no incluye cierres).'
DEF_OCULTA = 'Falla Oculta: la afluencia se comportó como en una falla, pero no hay reporte oficial del incidente.'
FUENTE = 'Fuente: afluencia diaria de SEMOVI (datos.cdmx.gob.mx) y bitácora OSINT del proyecto.'

def notas(fig, *lineas_texto):
    fig.text(0.01, 0.012, '\n'.join(lineas_texto), fontsize=8.5, color=TINTA2, va='bottom')

periodo = f"{pd.to_datetime(criticas['fecha']).min():%Y} a {pd.to_datetime(criticas['fecha']).max():%m/%Y}"

# ---------- 01. Lineas: pasajeros afectados por estacion y causa principal ----------
l = lineas.iloc[::-1]
fig, ax = plt.subplots(figsize=(12, 7))
y = np.arange(len(l))
for yi, (linea, f) in zip(y, l.iterrows()):
    barra_linea(ax, yi, f['pasajeros_afectados_por_estacion'] / 1000, linea)
for yi, (_, f) in zip(y, l.iterrows()):
    ax.text(f['pasajeros_afectados_por_estacion'] / 1000 + 6, yi,
            f"{f['dias_criticos']:.0f} días críticos · {f['pct_falsa_alarma_osint']:.0f}% falsas alarmas · causa principal: {f['causa_principal_osint']}",
            va='center', fontsize=9, color=TINTA2)
ax.set_yticks(y); ax.set_yticklabels([nombre_linea(i) for i in l.index], fontsize=11)
ax.set_xlim(0, l['pasajeros_afectados_por_estacion'].max() / 1000 * 2.05)
ax.set_xlabel('Pasajeros afectados por estación (miles), suma de la desviación en días críticos')
ax.xaxis.grid(True, color=REJILLA, linewidth=0.8); ax.set_axisbelow(True)
limpiar_ejes(ax)
fig.suptitle('¿Qué líneas son más conflictivas?', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.905, f'Anomalías críticas del detector, {periodo}. Se divide entre el número de estaciones para comparar líneas de distinto tamaño.',
         fontsize=10, color=TINTA2)
notas(fig, 'Falsas alarmas y causa principal según la OSINT de cada línea; la causa principal no cuenta las falsas alarmas.',
      DEF_CRITICO, DEF_OCULTA, FUENTE)
fig.tight_layout(rect=(0, 0.09, 1, 0.9))
fig.savefig(f'{IMG}/01_lineas_conflictivas.png', dpi=200)
plt.close(fig)

# ---------- 02. Causas por linea (OSINT) ----------
t = causas_linea_pct.loc[lineas.index]
cmap = LinearSegmentedColormap.from_list('azul', [FONDO, '#cde2fb', '#86b6ef', '#2a78d6', '#104281'])
fig, ax = plt.subplots(figsize=(16, 7.5))
ax.imshow(t.values, cmap=cmap, vmin=0, vmax=t.values.max(), aspect='auto')
for i in range(t.shape[0]):
    for j in range(t.shape[1]):
        v = t.values[i, j]
        ax.text(j, i, f'{v:.0f}%' if v else '·', ha='center', va='center', fontsize=9,
                color='white' if v > t.values.max() * 0.55 else (TINTA if v else '#a3a29c'))
ax.set_xticks(range(t.shape[1]))
ax.set_xticklabels([textwrap.fill(c, 13) for c in t.columns], fontsize=9)
ax.set_yticks(range(t.shape[0]))
ax.set_yticklabels([f"{nombre_linea(i)}  (n = {lineas.loc[i, 'registros_osint']:.0f})" for i in t.index], fontsize=10)
marcas_linea(ax, range(t.shape[0]), t.index, x=-0.004, ancho=0.008, alto=0.8)
ax.set_xticks(np.arange(-.5, t.shape[1], 1), minor=True); ax.set_yticks(np.arange(-.5, t.shape[0], 1), minor=True)
ax.grid(which='minor', color=FONDO, linewidth=2); ax.tick_params(which='both', length=0)
for s in ax.spines.values(): s.set_visible(False)
fig.suptitle('¿Por qué causas? Reparto de causas dentro de cada línea', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.92, f'Investigación OSINT de {len(osint)} anomalías críticas (muestra proporcional por línea). Cada fila suma 100%; n = registros investigados en la línea.',
         fontsize=10, color=TINTA2)
notas(fig, DEF_OCULTA + ' Falsa Alarma: se investigó y no se encontró causa.', FUENTE)
fig.tight_layout(rect=(0, 0.05, 1, 0.91))
fig.savefig(f'{IMG}/02_causas_por_linea.png', dpi=200)
plt.close(fig)

# ---------- 03. Estaciones mas conflictivas: caidas vs alzas ----------
e = estaciones.head(TOP_ESTACIONES).iloc[::-1]
fig, ax = plt.subplots(figsize=(13, 8))
y = np.arange(len(e))
# Caidas y alzas en grises para no confundirse con los colores de las lineas
ax.barh(y, e['pasajeros_en_caidas'] / 1e6, height=0.6, color='#4a4946', label='Pasajeros de menos (caídas)')
ax.barh(y, e['pasajeros_en_alzas'] / 1e6, left=e['pasajeros_en_caidas'] / 1e6, height=0.6, color='#bdbcb6',
        label='Pasajeros de más (alzas)')
for yi, (_, f) in zip(y, e.iterrows()):
    txt = f"{f['dias_criticos']:.0f} días críticos"
    if isinstance(f['causas_osint'], str):
        txt += ' · OSINT: ' + f['causas_osint']
    ax.text(f['pasajeros_afectados'] / 1e6 + 0.02, yi, txt, va='center', fontsize=8.5, color=TINTA2)
ax.set_yticks(y)
ax.set_yticklabels([f'{nombre_estacion(est)} ({nombre_linea(lin)})' for lin, est in e.index], fontsize=10)
marcas_linea(ax, y, [lin for lin, _ in e.index])
ax.set_xlim(0, e['pasajeros_afectados'].max() / 1e6 * 2.1)
ax.set_xlabel('Pasajeros afectados en días críticos (millones)')
ax.xaxis.grid(True, color=REJILLA, linewidth=0.8); ax.set_axisbelow(True)
limpiar_ejes(ax)
fig.suptitle(f'Las {TOP_ESTACIONES} estaciones con más pasajeros afectados por anomalías críticas', fontsize=15,
             fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.915, f'Detector Prophet + MAD, {periodo}. Entre paréntesis, causas encontradas por la OSINT en esa estación (número de registros).',
         fontsize=10, color=TINTA2)
fig.legend(loc='upper left', bbox_to_anchor=(0.005, 0.9), ncol=2, frameon=False, fontsize=10)
notas(fig, 'Pasajeros afectados: suma de la diferencia entre la afluencia real y la esperada por Prophet en los días críticos.', DEF_CRITICO, DEF_OCULTA, FUENTE)
fig.tight_layout(rect=(0, 0.08, 1, 0.86))
fig.savefig(f'{IMG}/03_estaciones_conflictivas.png', dpi=200)
plt.close(fig)

# ---------- 04. Efecto de cada causa en la afluencia ----------
ef = efecto_causa.iloc[::-1]
fig, ax = plt.subplots(figsize=(13, 7.5))
y = np.arange(len(ef))
for yi, (causa, f) in zip(y, ef.iterrows()):
    tenue = causa == RUIDO
    if f['caidas']:
        ax.barh(yi, f['cambio_mediano_en_caidas_pct'], height=0.6, color=GRIS if tenue else AZUL)
        ax.text(f['cambio_mediano_en_caidas_pct'] - 2, yi, f"{f['cambio_mediano_en_caidas_pct']:.0f}%  ({f['caidas']:.0f})",
                ha='right', va='center', fontsize=9, color=TINTA2)
    if f['alzas']:
        ax.barh(yi, f['cambio_mediano_en_alzas_pct'], height=0.6, color=GRIS if tenue else NARANJA)
        ax.text(f['cambio_mediano_en_alzas_pct'] + 2, yi, f"+{f['cambio_mediano_en_alzas_pct']:.0f}%  ({f['alzas']:.0f})",
                ha='left', va='center', fontsize=9, color=TINTA2)
ax.axvline(0, color=TINTA2, linewidth=1)
ax.set_yticks(y)
ax.set_yticklabels([f"{c}\n{f['pct_caidas']:.0f}% de las veces baja" for c, f in ef.iterrows()], fontsize=9.5)
lim = max(abs(ef['cambio_mediano_en_caidas_pct'].min()), ef['cambio_mediano_en_alzas_pct'].max()) * 1.45
ax.set_xlim(-lim, lim)
ax.set_xlabel('Cambio típico de la afluencia frente a lo esperado (mediana, %)')
ax.xaxis.grid(True, color=REJILLA, linewidth=0.8); ax.set_axisbelow(True)
limpiar_ejes(ax)
fig.suptitle('¿Cómo afecta cada causa a la afluencia?', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.915, 'Azul: cuando la causa bajó la afluencia. Naranja: cuando la subió. Entre paréntesis, número de registros OSINT. '
         'En gris, falsas alarmas como referencia.', fontsize=10, color=TINTA2)
notas(fig, 'Solo incluye días que el detector marcó como críticos: mide cuánto se movió la afluencia cuando la causa sí produjo una anomalía, '
      'no el efecto promedio de cada causa.', DEF_OCULTA, FUENTE)
fig.tight_layout(rect=(0, 0.07, 1, 0.9))
fig.savefig(f'{IMG}/04_efecto_por_causa.png', dpi=200)
plt.close(fig)
# ---------- 05. Causas ciclicas, programadas y esporadicas por linea ----------
t5 = tipo_linea_pct.loc[['Alertas de la predicción 2026', 'Toda la red'] + list(lineas.index)].iloc[::-1]
COLOR_TIPO = {'Cíclica': AZUL, 'Programada': '#9ec5f4', 'Esporádica': NARANJA, 'Falsa alarma': '#d6d5d0'}
TINTA_TIPO = {'Cíclica': 'white', 'Programada': TINTA, 'Esporádica': TINTA, 'Falsa alarma': TINTA}
ETIQ_TIPO = {'Cíclica': 'Cíclica (feriados, lluvias, contingencias)', 'Programada': 'Programada (eventos, cierres, elecciones)',
             'Esporádica': 'Esporádica (fallas, incidentes)', 'Falsa alarma': 'Falsa alarma'}
fig, ax = plt.subplots(figsize=(13, 7.5))
y = np.arange(len(t5))
izq = np.zeros(len(t5))
for tipo in TIPOS:
    v = t5[tipo].values
    ax.barh(y, v, left=izq, height=0.62, color=COLOR_TIPO[tipo], edgecolor=FONDO, linewidth=1.5, label=ETIQ_TIPO[tipo])
    for yi, vi, li in zip(y, v, izq):
        if vi >= 7:
            ax.text(li + vi / 2, yi, f'{vi:.0f}%', ha='center', va='center', fontsize=9, color=TINTA_TIPO[tipo])
    izq += v
ax.set_yticks(y)
ax.set_yticklabels([(i if not i.startswith('linea') else nombre_linea(i)) + f"  (n = {tipo_linea.loc[i].sum()})" for i in t5.index],
                   fontsize=10)
marcas_linea(ax, y, t5.index)
for lbl in ax.get_yticklabels():
    if not lbl.get_text().startswith('Línea'):
        lbl.set_fontweight('bold')
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
limpiar_ejes(ax, ('top', 'right', 'left', 'bottom'))
fig.suptitle('¿Qué parte de las anomalías se puede prevenir?', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.905, 'Causas encontradas por la OSINT, agrupadas por si se repiten con el calendario, se anuncian antes o son imprevistas. '
         'Líneas ordenadas por pasajeros afectados.', fontsize=10, color=TINTA2)
fig.legend(loc='upper left', bbox_to_anchor=(0.005, 0.89), ncol=4, frameon=False, fontsize=9.5)
sin_causa_pred = int(pred_tipo.isna().sum())
notas(fig, f'Histórico: {len(osint)} anomalías críticas 2022 a mar-2026. Predicción: {len(pred)} días que el modelo XGBoost marcó en alerta, ago a nov 2026'
      + (f' ({sin_causa_pred} sin causa registrada en la bitácora no se clasifican).' if sin_causa_pred else '.'),
      'Cíclica: se repite con el calendario. Programada: se anuncia con anticipación. Esporádica: no se puede anticipar.', FUENTE)
fig.tight_layout(rect=(0, 0.07, 1, 0.87))
fig.savefig(f'{IMG}/05_causas_ciclicas_y_esporadicas.png', dpi=200)
plt.close(fig)
print(f'Gráficas guardadas en {IMG}/ y tablas en {RES}/')

# Historial: tablas a historico/ (git) y graficas a historico_local/
registrar_corrida(
    'estaciones_y_causas',
    archivos=sorted(f'{RES}/{f}' for f in os.listdir(RES) if f.endswith('.csv')),
    archivos_locales=sorted(f'{IMG}/{f}' for f in os.listdir(IMG) if f.endswith('.png')),
    metricas={'lineas_mas_afectadas_por_estacion': lineas.index[:3].tolist(),
              'anomalias_osint': len(osint)},
)
