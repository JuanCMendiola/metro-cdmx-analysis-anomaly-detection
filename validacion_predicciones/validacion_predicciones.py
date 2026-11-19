# %% [markdown]
# Validacion de las predicciones de anomalias futuras (XGBoost).
# Calcula las tasas de la OSINT por estrato (y ponderadas), cruza los dias en
# alerta con la afluencia real publicada por SEMOVI y genera las graficas.
# La investigacion OSINT es manual: este script solo la lee, no la genera.
# Ejecutar desde la raiz del repo:  python validacion_predicciones/validacion_predicciones.py
# Metodologia y lectura de resultados: validacion_predicciones/ANALISIS.md

# %%
import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

CARPETA = 'validacion_predicciones'
DATOS = f'{CARPETA}/datos'
IMG = f'{CARPETA}/img'
RES = f'{CARPETA}/resultados'
os.makedirs(IMG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

BITACORA_PRED = f'{DATOS}/bitacora_validacion_predicciones_final.csv'      # OSINT manual consolidada (79 filas)
BITACORA_HIST = 'bitacora_investigacion_anomalias_criticas.csv'             # OSINT manual del historico (raiz del repo)
CORRIDA = f'{DATOS}/propuesta_anomalias_futuras_corrida_validacion.xlsx'    # corrida del modelo de la que salio la muestra
SEMOVI = f'{DATOS}/afluenciastc_desglosado_2026-01_a_2026-09.csv'          # afluencia real 2026 (datos.cdmx.gob.mx)

FECHA_CORTE = '2026-11-05'       # ultimo dia ya ocurrido cuando se sorteo la muestra
INICIO_REAL = '2026-08-02'       # primer dia en alerta de la corrida
TASA_HISTORICA = 3.0             # % de estacion-dias CRITICOS en el historico (modeling/ANALISIS.md: 2.6% a 3.3%)
ESTRATOS = ['A - Alta', 'B - Media', 'C - Control']
NOMBRES = {'A - Alta': 'Riesgo alto', 'B - Media': 'Riesgo medio', 'C - Control': 'Riesgo bajo'}

# %% [markdown]
# ## 1. Universo y estratos (mismo criterio que el muestreo de la corrida)
# A = prob_critica >= P90, B = P75 a P90, C = < P75, sobre los dias en alerta
# con fecha <= corte. N_h es el tamano de cada estrato en ese universo.

# %%
alertas = pd.read_excel(CORRIDA, sheet_name='Dias en alerta')
alertas['fecha'] = pd.to_datetime(alertas['fecha'])
universo = alertas[alertas['fecha'] <= FECHA_CORTE]
P90 = universo['prob_critica'].quantile(0.90)
P75 = universo['prob_critica'].quantile(0.75)

def estrato(prob):
    return np.where(prob >= P90, 'A - Alta', np.where(prob >= P75, 'B - Media', 'C - Control'))

N_h = pd.Series(estrato(universo['prob_critica'])).value_counts().reindex(ESTRATOS)
N = N_h.sum()
print(f'Universo: {N} dias en alerta hasta {FECHA_CORTE}; P90 = {P90:.4f}, P75 = {P75:.4f}')
print(N_h.to_string())

# %% [markdown]
# ## 2. Tasas de la OSINT por estrato y ponderadas
# Tasa Si = filas "Si" / filas revisadas del estrato; Si+Parcial igual.
# Ponderada = suma de N_h * tasa_h / N (el estrato A esta sobrerrepresentado
# en la muestra porque se investigo completo).

# %%
pred = pd.read_csv(BITACORA_PRED)
pred['respuesta'] = pred['Ocurrio_Evento'].str.split(' - ').str[0].str.strip()
conteo = pd.crosstab(pred['Estrato'], pred['respuesta']).reindex(ESTRATOS, fill_value=0)
for col in ['Sí', 'Parcial', 'No', 'Sin información suficiente']:
    if col not in conteo:
        conteo[col] = 0
tasas = pd.DataFrame({
    'N_h_universo': N_h,
    'n_h_muestra': conteo.sum(axis=1),
    'si': conteo['Sí'],
    'parcial': conteo['Parcial'],
    'no': conteo['No'],
    'sin_informacion': conteo['Sin información suficiente'],
})
tasas['tasa_si_pct'] = tasas['si'] / tasas['n_h_muestra'] * 100
tasas['tasa_si_parcial_pct'] = (tasas['si'] + tasas['parcial']) / tasas['n_h_muestra'] * 100
tasas['peso_N_h_N'] = tasas['N_h_universo'] / N
ponderada = pd.DataFrame({
    'N_h_universo': [N], 'n_h_muestra': [tasas['n_h_muestra'].sum()],
    'si': [tasas['si'].sum()], 'parcial': [tasas['parcial'].sum()], 'no': [tasas['no'].sum()],
    'sin_informacion': [tasas['sin_informacion'].sum()],
    'tasa_si_pct': [(tasas['tasa_si_pct'] * tasas['peso_N_h_N']).sum()],
    'tasa_si_parcial_pct': [(tasas['tasa_si_parcial_pct'] * tasas['peso_N_h_N']).sum()],
    'peso_N_h_N': [1.0],
}, index=['Ponderada (universo)'])
tasas = pd.concat([tasas, ponderada]).round(3)
tasas.index.name = 'estrato'
tasas.to_csv(f'{RES}/tasas_osint_por_estrato.csv', encoding='utf-8-sig')
print(tasas[['n_h_muestra', 'si', 'parcial', 'no', 'tasa_si_pct', 'tasa_si_parcial_pct']].round(1).to_string())

causas = pred['Hallazgo_Principal'].str.strip().value_counts().rename('registros').to_frame()
causas['pct'] = (causas['registros'] / len(pred) * 100).round(1)
causas.index.name = 'causa'
causas.to_csv(f'{RES}/causas_osint_prediccion.csv', encoding='utf-8-sig')

# %% [markdown]
# ## 3. Afluencia real (SEMOVI) en los dias en alerta
# Se aplica a la afluencia real el mismo detector del repo (modeling/prophet_mad.py):
# cierre = 0 o < 5% de la mediana de los 5 dias equivalentes previos; MAD estacional
# (5 semanas del mismo dia, |z| > 3.5); Prophet = fuera de la banda yhat_lower/yhat_upper
# que pronostico la corrida; CRITICA = MAD y Prophet.

# %%
def limpiar_texto(texto):
    # Igual que data/recoleccion_y_limpieza.py: corrige el texto mal codificado y quita acentos de "Linea"
    try:
        texto = texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    texto = unicodedata.normalize('NFC', texto).replace('Línea', 'Linea').replace('linea', 'Linea')
    return texto.lower()

real = pd.read_csv(SEMOVI, encoding='utf-8')
real['fecha'] = pd.to_datetime(real['fecha'])
real['linea'] = real['linea'].map(limpiar_texto)
real['estacion'] = real['estacion'].map(limpiar_texto)
real = (real.groupby(['fecha', 'linea', 'estacion'])['afluencia'].sum().reset_index()
            .sort_values(['linea', 'estacion', 'fecha']).reset_index(drop=True))
ULTIMO_REAL = real['fecha'].max()

grupos = [real['linea'], real['estacion'], real['fecha'].dt.dayofweek]
def movil_sin_cierres(serie, calculo):
    return serie.groupby(grupos).transform(lambda x: calculo(x.dropna()).reindex(x.index))
def mediana_movil_5(x):
    return x.rolling(window=5, min_periods=3).median().shift(1)
def calc_mad_vectorizada(x):
    mediana = x.rolling(window=5, min_periods=3).median().shift(1)
    return (x.shift(1) - mediana).abs().rolling(window=5, min_periods=3).median()

referencia = movil_sin_cierres(real['afluencia'].where(real['afluencia'] > 0), mediana_movil_5)
real['es_cierre'] = (real['afluencia'] == 0) | (real['afluencia'] < 0.05 * referencia)
valida = real['afluencia'].where(~real['es_cierre'])
real['mediana_movil'] = movil_sin_cierres(valida, mediana_movil_5)
real['mad_movil'] = movil_sin_cierres(valida, calc_mad_vectorizada)
real['zscore_robusto'] = (real['afluencia'] - real['mediana_movil']) / (real['mad_movil'] * 1.4826 + 1e-6)
real['anomalia_mad'] = (real['zscore_robusto'].abs() > 3.5) & ~real['es_cierre']

cruce = alertas[(alertas['fecha'] >= INICIO_REAL) & (alertas['fecha'] <= ULTIMO_REAL)].merge(
    real, on=['fecha', 'linea', 'estacion'], how='left')
sin_dato = cruce['afluencia'].isna().sum()
cruce = cruce[cruce['afluencia'].notna()].copy()
cruce['anomalia_prophet'] = (cruce['afluencia'] < cruce['yhat_lower']) | (cruce['afluencia'] > cruce['yhat_upper'])
cruce['estrato'] = estrato(cruce['prob_critica'])
cruce['etiqueta'] = np.select(
    [cruce['es_cierre'], cruce['anomalia_prophet'] & cruce['anomalia_mad'], cruce['anomalia_prophet'], cruce['anomalia_mad']],
    ['CIERRE (Operativo)', 'CRÍTICA (Consenso)', 'ALTA (Solo Prophet)', 'MEDIA (Solo MAD)'], 'Normal')
cruce['critica'] = cruce['etiqueta'].str.startswith('CRÍTICA')
cruce['cualquier_anomalia'] = ~cruce['etiqueta'].isin(['Normal', 'CIERRE (Operativo)'])   # un cierre no cuenta como anomalia
cruce['dif_vs_esperada_pct'] = (cruce['afluencia'] / cruce['afluencia_esperada_prophet'] - 1) * 100
(cruce[['fecha', 'linea', 'estacion', 'estrato', 'prob_critica', 'riesgo_vs_mismo_dia', 'afluencia_esperada_prophet',
        'yhat_lower', 'yhat_upper', 'afluencia', 'dif_vs_esperada_pct', 'zscore_robusto', 'etiqueta']]
    .rename(columns={'afluencia': 'afluencia_real_semovi'}).round({'prob_critica': 4, 'riesgo_vs_mismo_dia': 3, 'dif_vs_esperada_pct': 1, 'zscore_robusto': 2})
    .to_csv(f'{RES}/dias_en_alerta_vs_afluencia_real.csv', index=False, encoding='utf-8-sig'))
print(f'Dias en alerta con dato real ({INICIO_REAL} a {ULTIMO_REAL.date()}): {len(cruce)}; sin dato: {sin_dato}')

def resumen_real(df):
    return pd.Series({'dias_en_alerta': len(df), 'criticas': int(df['critica'].sum()),
                      'tasa_critica_pct': df['critica'].mean() * 100,
                      'cualquier_anomalia_pct': df['cualquier_anomalia'].mean() * 100,
                      'dentro_de_banda_pct': (~df['anomalia_prophet']).mean() * 100,
                      'dif_mediana_vs_esperada_pct': df['dif_vs_esperada_pct'].median()})
COLS_REAL = ['critica', 'cualquier_anomalia', 'anomalia_prophet', 'dif_vs_esperada_pct']
tasas_real = cruce.groupby('estrato')[COLS_REAL].apply(resumen_real).reindex(ESTRATOS)
tasas_real.loc['Todos los dias en alerta'] = resumen_real(cruce)
tasas_real.loc['Todos sin el 16-sep'] = resumen_real(cruce[cruce['fecha'] != '2026-09-16'])
tasas_real.index.name = 'estrato'
tasas_real.round(1).to_csv(f'{RES}/tasas_afluencia_real_por_estrato.csv', encoding='utf-8-sig')
print(tasas_real.round(1).to_string())

# %% [markdown]
# ## 4. Graficas

# %%
TINTA, TINTA2, FONDO, REJILLA = '#0b0b0b', '#52514e', '#fcfcfb', '#e4e3df'
AZUL, AZUL_CLARO, GRIS, GRIS_CLARO, NARANJA = '#2a78d6', '#9ec5f4', '#c9c8c2', '#e9e8e4', '#eb6834'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': FONDO, 'axes.facecolor': FONDO,
                     'text.color': TINTA, 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA,
                     'axes.edgecolor': REJILLA})

def cargar_bitacora(ruta):
    df = pd.read_csv(ruta)
    df.columns = df.columns.str.lower()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['causa'] = df['hallazgo_principal'].str.strip()
    return df

hist, pr = cargar_bitacora(BITACORA_HIST), cargar_bitacora(BITACORA_PRED)
orden = hist['causa'].value_counts().index.tolist()
orden += [c for c in pr['causa'].value_counts().index if c not in orden]
MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
fin_hist = hist['fecha'].max()
periodo_hist = f"{hist['fecha'].min().year} a {MESES[fin_hist.month - 1].lower()} {fin_hist.year}"

# ---------- 01. Clasificacion de causas: % del historico vs % de la prediccion ----------
ch = hist['causa'].value_counts().reindex(orden, fill_value=0)
cp = pr['causa'].value_counts().reindex(orden, fill_value=0)
ph, pp = ch / len(hist) * 100, cp / len(pr) * 100
y = np.arange(len(orden))[::-1]
alto = 0.38
fig, ax = plt.subplots(figsize=(12, 8))
b1 = ax.barh(y + alto / 2 + 0.02, ph, height=alto, color=AZUL, label=f'Anomalías históricas, {periodo_hist} (n = {len(hist)})')
b2 = ax.barh(y - alto / 2 - 0.02, pp, height=alto, color=NARANJA, label=f'Alertas de la predicción, ago a nov 2026 (n = {len(pr)})')
for barras, cuenta, pct in ((b1, ch, ph), (b2, cp, pp)):
    for rect, n, p in zip(barras, cuenta, pct):
        ax.text(rect.get_width() + 0.4, rect.get_y() + rect.get_height() / 2, f'{n} ({p:.1f}%)',
                va='center', ha='left', fontsize=9, color=TINTA2)
ax.set_yticks(y); ax.set_yticklabels(orden, fontsize=10)
ax.set_xlabel('Porcentaje de los registros investigados (%)')
ax.set_xlim(0, max(ph.max(), pp.max()) + 6)
ax.xaxis.grid(True, color=REJILLA, linewidth=0.8); ax.set_axisbelow(True)
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.tick_params(axis='y', length=0)
fig.suptitle('Clasificación de causas (OSINT): histórico vs predicción', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.legend(loc='upper left', bbox_to_anchor=(0.005, 0.945), ncol=2, frameon=False, fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(f'{IMG}/01_causas_historico_vs_prediccion.png', dpi=200)
plt.close(fig)

# ---------- 02. Calendario de riesgo: causa x mes, historico y prediccion ----------
def tabla_mes(df, meses):
    return pd.crosstab(df['causa'], df['fecha'].dt.month).reindex(index=orden, columns=meses, fill_value=0)
th = tabla_mes(hist, range(1, 13))
meses_pred = sorted(pr['fecha'].dt.month.unique())
tp = tabla_mes(pr, meses_pred)
cmap = LinearSegmentedColormap.from_list('azul', [FONDO, '#cde2fb', '#86b6ef', '#2a78d6', '#104281'])

def mapa(ax, t, etiquetas_mes, titulo, mostrar_y):
    vmax = max(t.values.max(), 1)
    ax.imshow(t.values, cmap=cmap, vmin=0, vmax=vmax, aspect='auto')
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            v = t.values[i, j]
            ax.text(j, i, str(v), ha='center', va='center', fontsize=10,
                    color='white' if v > vmax * 0.55 else (TINTA if v else '#a3a29c'))
    ax.set_xticks(range(t.shape[1])); ax.set_xticklabels(etiquetas_mes, fontsize=10)
    ax.set_yticks(range(t.shape[0])); ax.set_yticklabels(t.index if mostrar_y else [], fontsize=10)
    ax.set_xticks(np.arange(-.5, t.shape[1], 1), minor=True); ax.set_yticks(np.arange(-.5, t.shape[0], 1), minor=True)
    ax.grid(which='minor', color=FONDO, linewidth=2); ax.tick_params(which='both', length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title(titulo, fontsize=12, fontweight='bold', loc='left', pad=10)
    ax.set_xlabel('Mes del año')

fig, (a1, a2) = plt.subplots(1, 2, figsize=(17, 7.5), gridspec_kw={'width_ratios': [12, len(meses_pred)], 'wspace': 0.05})
mapa(a1, th, MESES, f'Anomalías críticas históricas, {periodo_hist}\n(n = {len(hist)})', True)
mapa(a2, tp, [MESES[m - 1] for m in meses_pred], f'Alertas de la predicción, 2026\n(n = {len(pr)})', False)
fig.suptitle('Calendario de riesgo (estacionalidad de anomalías por causa): histórico vs predicción',
             fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.01, 'Cada celda es el número de registros investigados. Cada panel tiene su propia escala de color (más oscuro = más registros dentro de ese panel).',
         fontsize=9, color=TINTA2)
fig.subplots_adjust(left=0.27, right=0.99, top=0.84, bottom=0.12)
fig.savefig(f'{IMG}/02_calendario_riesgo_historico_vs_prediccion.png', dpi=200)
plt.close(fig)

# ---------- 03. OSINT: que se encontro en los dias que el modelo marco ----------
RESP = [('Sí', 'Evento en la estación o en su línea', AZUL, 'white'),
        ('Parcial', 'Evento cercano o de toda la ciudad (feriado, lluvia)', AZUL_CLARO, TINTA),
        ('No', 'No se encontró nada', GRIS, TINTA),
        ('Sin información suficiente', 'Sin información suficiente', GRIS_CLARO, TINTA)]
t = conteo[[r[0] for r in RESP]]
pct = t.div(t.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(12, 5.2))
y = np.arange(len(ESTRATOS))[::-1]
izq = np.zeros(len(ESTRATOS))
for clave, etiqueta, color, tinta in RESP:
    v = pct[clave].values
    ax.barh(y, v, left=izq, height=0.56, color=color, edgecolor=FONDO, linewidth=2, label=etiqueta)
    for yi, vi, li, n in zip(y, v, izq, t[clave].values):
        if vi >= 6:
            ax.text(li + vi / 2, yi, f'{vi:.0f}%\n({n})', ha='center', va='center', fontsize=10, color=tinta)
    izq += v
ax.set_yticks(y)
ax.set_yticklabels([f'{NOMBRES[e]}\n{t.loc[e].sum()} días revisados' for e in ESTRATOS], fontsize=11)
ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
ax.set_xlabel('Porcentaje de los días revisados en cada nivel de riesgo')
for s in ('top', 'right', 'left', 'bottom'): ax.spines[s].set_visible(False)
ax.tick_params(length=0)
fechas_alto = pred.loc[pred['Estrato'] == 'A - Alta', 'Fecha'].nunique()
fig.suptitle('¿Qué encontramos en los días que el modelo marcó en alerta?', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.90, f'Búsqueda manual de noticias (OSINT) en {len(pred)} estación-días en alerta, ago a nov 2026, según el nivel de riesgo que les dio el modelo',
         fontsize=10, color=TINTA2)
fig.legend(loc='upper left', bbox_to_anchor=(0.005, 0.88), ncol=4, frameon=False, fontsize=10)
fig.text(0.01, 0.02, f'Los días de riesgo alto son solo {fechas_alto} fechas: 16 de septiembre (Independencia) y 2 de noviembre (Día de Muertos).',
         fontsize=9, color=TINTA2)
fig.tight_layout(rect=(0, 0.05, 1, 0.8))
fig.savefig(f'{IMG}/03_osint_por_nivel_de_riesgo.png', dpi=200)
plt.close(fig)

# ---------- 04. SEMOVI: la afluencia real fue anormal en los dias marcados? ----------
g = cruce.groupby('estrato')['critica'].agg(['sum', 'count']).reindex(ESTRATOS)
tasa = g['sum'] / g['count'] * 100
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(ESTRATOS))
ax.bar(x, tasa.values, width=0.5, color=AZUL)
for xi, ti, s, c in zip(x, tasa.values, g['sum'], g['count']):
    ax.text(xi, ti + 1, f'{ti:.0f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')
    ax.text(xi, ti + 4.2, f'{s} de {c} días', ha='center', va='bottom', fontsize=10, color=TINTA2)
ax.axhline(TASA_HISTORICA, color=NARANJA, linewidth=2, linestyle='--')
ax.text(1.5, TASA_HISTORICA + 0.8, f'Un día cualquiera:\ncerca de {TASA_HISTORICA:.0f}%', ha='center', va='bottom',
        fontsize=10, color=TINTA, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([NOMBRES[e] for e in ESTRATOS], fontsize=12)
ax.set_ylim(0, max(tasa.max() + 9, 20)); ax.set_ylabel('Días con afluencia anormal (%)')
ax.yaxis.grid(True, color=REJILLA, linewidth=0.8); ax.set_axisbelow(True)
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.tick_params(length=0)
total = g['sum'].sum() / g['count'].sum() * 100
alto_16 = (cruce.loc[cruce['estrato'] == 'A - Alta', 'fecha'] == '2026-09-16').all()
MESES_LARGOS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
ini, fin = pd.Timestamp(INICIO_REAL), ULTIMO_REAL
fig.suptitle('¿La afluencia fue realmente anormal en los días en alerta?', fontsize=15, fontweight='bold', x=0.01, ha='left')
fig.text(0.01, 0.90, f'Afluencia real (SEMOVI) en {int(g["count"].sum())} estación-días en alerta, del {ini.day} de {MESES_LARGOS[ini.month - 1]} '
         f'al {fin.day} de {MESES_LARGOS[fin.month - 1]} de {fin.year}. Todos los días en alerta juntos: {total:.0f}%', fontsize=10, color=TINTA2)
nota = 'Anormal = anomalía crítica: la afluencia salió del rango esperado y se alejó de su patrón semanal reciente.'
if alto_16:
    nota += f'\nLos {int(g.loc["A - Alta", "count"])} días de riesgo alto son del 16 de septiembre (Independencia), cuando la afluencia cayó en toda la red.'
fig.text(0.01, 0.02, nota, fontsize=9, color=TINTA2)
fig.tight_layout(rect=(0, 0.08, 1, 0.9))
fig.savefig(f'{IMG}/04_afluencia_real_por_nivel_de_riesgo.png', dpi=200)
plt.close(fig)
print(f'Gráficas guardadas en {IMG}/ y tablas en {RES}/')
