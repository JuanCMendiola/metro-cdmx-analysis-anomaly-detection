# %%
# Motor de auditoria de las 195 series: Z-score robusto (MAD estacional) + Prophet
# por estacion, con consenso de prioridades (CRITICA / ALTA / MEDIA / CIERRE).
# Antes vivia dentro de modeling/modelado.ipynb; se separo para que el notebook
# no reentrene 195 Prophet ni reescriba las 196 graficas en cada corrida (y git
# no las vea como cambios cada vez). Correr solo cuando haya datos nuevos o se
# cambie el detector.
# Contexto y criterios: ver ANALISIS.md (esta misma carpeta) y las celdas de
# markdown de modelado.ipynb.
# Entradas: data/processed/dataset_original_copy.pkl
# Salidas:  master_auditoria_consenso_MAD.csv/.xlsx (raiz del repo),
#           data/processed/prophet_series.pkl (insumo del modelo de riesgo del notebook),
#           modeling/img_pronosticos/<linea>/<estacion>.png
#
# Correr con la raiz del repo como working directory:
#   python modeling/prophet_mad.py

import io
import os
import re
import unicodedata
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from prophet import Prophet

GENERAR_GRAFICAS = True   # False: recalcula datos sin regenerar las imagenes

dataset_original_copy = pd.read_pickle('data/processed/dataset_original_copy.pkl')

# %%
# Z-score robusto con MAD estacional (mismo dia de la semana) y cierres operativos
# 1. Se parte nuevamente del dataset limpio (agrupado por día)
df_limpio = dataset_original_copy.groupby(['fecha', 'linea', 'estacion'])['afluencia'].sum().reset_index()

# Garantizar tipo datetime y ORDEN temporal estricto antes de aplicar ventanas móviles
df_limpio['fecha'] = pd.to_datetime(df_limpio['fecha'])
df_limpio = df_limpio.sort_values(by=['linea', 'estacion', 'fecha']).reset_index(drop=True)

# Copia de seguridad del dataset limpio
df_limpio_copy = df_limpio.copy()

# Generar día de la semana para evaluar estacionalidad equivalente (Lunes vs Lunes pasados, etc.)
df_limpio['_dia_semana'] = df_limpio['fecha'].dt.dayofweek
grupos_dia = [df_limpio['linea'], df_limpio['estacion'], df_limpio['_dia_semana']]

def movil_sin_cierres(serie, calculo):
    # Ventana móvil solo sobre los días válidos (sin cierres) de cada estación y día de la semana:
    # un cierre no entra a la referencia y la reapertura se compara contra los últimos días
    # normales, no contra una ventana llena de ceros. Los días de cierre quedan en NaN.
    return serie.groupby(grupos_dia).transform(lambda x: calculo(x.dropna()).reindex(x.index))

def mediana_movil_5(x):
    return x.rolling(window=5, min_periods=3).median().shift(1)

# 2. Cierres operativos (mantenimiento, obras, cierres por eventos como el Grito en Zócalo):
#    días en 0 o con menos del 5% de la afluencia normal de ese día de la semana.
#    No son anomalías de demanda: se excluyen de las ventanas móviles y de Prophet,
#    y se etiquetan aparte como CIERRE (Operativo).
UMBRAL_CIERRE = 0.05
referencia = movil_sin_cierres(df_limpio['afluencia'].where(df_limpio['afluencia'] > 0), mediana_movil_5)
df_limpio['es_cierre'] = (df_limpio['afluencia'] == 0) | (df_limpio['afluencia'] < UMBRAL_CIERRE * referencia)
afluencia_valida = df_limpio['afluencia'].where(~df_limpio['es_cierre'])
print(f"Días de cierre operativo: {df_limpio['es_cierre'].sum():,} de {len(df_limpio):,} "
      f"({df_limpio['es_cierre'].mean()*100:.2f}%)")

# 3. Cálculo Media y Desviación Estándar Móvil (Ventana 5 semanas equivalentes, con shift para no ver el futuro)
df_limpio['media_movil'] = movil_sin_cierres(afluencia_valida, lambda x: x.rolling(window=5, min_periods=3).mean().shift(1))
df_limpio['std_movil'] = movil_sin_cierres(afluencia_valida, lambda x: x.rolling(window=5, min_periods=3).std().shift(1))

# 4. Recálculo de Z-Score Clásico (con protección contra división por cero)
epsilon = 1e-6
df_limpio['zscore_movil'] = (df_limpio['afluencia'] - df_limpio['media_movil']) / (df_limpio['std_movil'] + epsilon)

# 5. Generamos la bandera booleana de anomalía (detecta tanto alzas como bajas)
df_limpio['anomalia_z'] = df_limpio['zscore_movil'].abs() > 3

# --- Calcular MAD ---
# Mediana móvil
df_limpio['mediana_movil'] = movil_sin_cierres(afluencia_valida, mediana_movil_5)

# Cálculo vectorizado y rápido de la MAD
def calc_mad_vectorizada(series, window, min_periods):
    mediana = series.rolling(window=window, min_periods=min_periods).median().shift(1)
    dev_absoluta = (series.shift(1) - mediana).abs()
    return dev_absoluta.rolling(window=window, min_periods=min_periods).median()

df_limpio['mad_movil'] = movil_sin_cierres(afluencia_valida, lambda x: calc_mad_vectorizada(x, window=5, min_periods=3))

# Z-Score Robusto con MAD
df_limpio['zscore_robusto'] = (df_limpio['afluencia'] - df_limpio['mediana_movil']) / ((df_limpio['mad_movil'] * 1.4826) + epsilon)

# Bandera de anomalía robusta (detecta alzas y bajas); un cierre no es anomalía de demanda
df_limpio['anomalia_mad'] = (df_limpio['zscore_robusto'].abs() > 3.5) & ~df_limpio['es_cierre']

# Limpiar columna auxiliar de apoyo
df_limpio.drop(columns=['_dia_semana'], inplace=True)

# %%
# Prophet por estacion + consenso con MAD
DIAS_FUTURO = 182   # horizonte del pronostico de Prophet: 6 meses (antes 90 dias)

COLORES_PRIORIDAD = {
    'CRÍTICA (Consenso)': '#8B0000',
    'ALTA (Solo Prophet)': '#FF8C00',
    'MEDIA (Solo MAD)': '#C9B800',
    'CIERRE (Operativo)': '#7F7F7F'
}

def guardar_png_ligero(fig, ruta, dpi=80):
    # ~1200 px de ancho y paleta de 256 colores sin tramado: ~130 KB por grafica en vez de ~500 KB,
    # sin perder los colores de las prioridades
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    img.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(ruta, optimize=True)

def _slug(texto):
    # 'boulevard puerto aéreo' -> 'boulevard_puerto_aereo' (nombre de archivo seguro)
    t = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', t.lower()).strip('_')

def _dibujar_pronostico(ax, df_hist, df_futuro, tam_punto, grosor):
    ax.plot(df_hist['ds'], df_hist['afluencia'], color='black', linewidth=grosor, label='Afluencia real')
    ax.plot(df_hist['ds'], df_hist['yhat'], color='blue', linewidth=grosor, label='Prophet (ajuste)')
    ax.fill_between(df_hist['ds'], df_hist['yhat_lower'], df_hist['yhat_upper'],
                    color='blue', alpha=0.15, label='Intervalo de confianza')

    for prioridad, color in COLORES_PRIORIDAD.items():
        sel = df_hist[df_hist['prioridad_auditoria'] == prioridad]
        if len(sel):
            ax.scatter(sel['ds'], sel['afluencia'], s=tam_punto, color=color, zorder=3,
                       label=f'{prioridad} ({len(sel)})')

    if len(df_futuro):
        ax.plot(df_futuro['ds'], df_futuro['yhat'], color='green', linestyle='--', linewidth=1.5,
                label=f'Pronóstico próximos {len(df_futuro)} días')
        ax.fill_between(df_futuro['ds'], df_futuro['yhat_lower'], df_futuro['yhat_upper'],
                        color='green', alpha=0.2)
        ax.axvline(df_hist['ds'].max(), color='gray', linestyle=':', linewidth=1)

    ax.set_ylabel('Afluencia diaria (pasajeros)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.grid(True, alpha=0.3)

def graficar_pronostico_serie(linea, estacion, df_hist, df_futuro, carpeta, dias_zoom=90):
    """Guarda una grafica por serie: arriba todo el historico, abajo zoom a los ultimos dias + pronostico."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    _dibujar_pronostico(ax1, df_hist, df_futuro, tam_punto=8, grosor=0.7)
    ax1.set_title(f'Pronóstico Prophet: {linea} - {estacion}', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8, ncol=2)

    zoom = df_hist[df_hist['ds'] > df_hist['ds'].max() - pd.Timedelta(days=dias_zoom)]
    _dibujar_pronostico(ax2, zoom, df_futuro, tam_punto=28, grosor=1.3)
    ax2.set_title(f'Zoom: últimos {dias_zoom} días + pronóstico', fontsize=11)
    ax2.set_xlabel('Fecha')

    ruta = os.path.join(carpeta, _slug(linea), f'{_slug(estacion)}.png')
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.tight_layout()
    guardar_png_ligero(fig, ruta)
    plt.close(fig)
    return ruta

def motor_auditoria_consenso_mad_bidireccional(df_input, carpeta_graficas='modeling/img_pronosticos', dias_futuro=DIAS_FUTURO):
    # carpeta_graficas=None desactiva las graficas; dias_futuro=0 quita el pronostico a futuro
    resultados_master = []
    series_prophet = []   # pronostico completo (historico + futuro) de cada serie, para el modelo de riesgo
    grupos = df_input.groupby(['linea', 'estacion'])
    total = len(grupos)

    print(f"Iniciando auditoría masiva bidireccional para {total} estaciones...")

    for i, ((linea, estacion), df_grupo) in enumerate(grupos, 1):
        try:
            df_p = df_grupo.copy()
            if 'fecha' not in df_p.columns: df_p = df_p.reset_index()
            df_prophet = df_p[['fecha', 'afluencia']].rename(columns={'fecha': 'ds', 'afluencia': 'y'})

            # No se entrena con dias de cierre operativo (afluencia 0 o casi 0): sesgarian
            # la tendencia/estacionalidad hacia abajo y harian que el efecto de un festivo
            # (p. ej. 16 de septiembre en Zocalo) saliera como miles de pasajeros negativos.
            # Se predice sobre TODOS los dias; los cierres se etiquetan aparte como CIERRE.
            df_prophet_train = df_prophet[~df_p['es_cierre'].values]

            # Instanciación de Prophet con intervalo de confianza del 95% (Evita falsos positivos)
            m = Prophet(
                yearly_seasonality=True, 
                weekly_seasonality=True, 
                changepoint_prior_scale=0.03,
                interval_width=0.95  # <--- Agregado para mayor robustez en bandas upper/lower
                )
            m.add_country_holidays(country_name='MX')
            m.fit(df_prophet_train)

            # Una sola prediccion sobre historico + dias futuros; el tramo historico
            # es el mismo de siempre, el futuro solo alimenta la grafica de pronostico.
            ds_hist = df_prophet['ds']
            ds_futuro = pd.date_range(ds_hist.max() + pd.Timedelta(days=1), periods=dias_futuro, freq='D')
            forecast_total = m.predict(pd.DataFrame({'ds': list(ds_hist) + list(ds_futuro)}))
            # La afluencia no puede ser negativa: el modelo aditivo puede cruzar el 0 en estaciones de poca demanda
            forecast_total[['yhat', 'yhat_lower', 'yhat_upper']] = forecast_total[['yhat', 'yhat_lower', 'yhat_upper']].clip(lower=0)
            forecast = forecast_total.iloc[:len(ds_hist)]
            forecast_futuro = forecast_total.iloc[len(ds_hist):]

            # Asegurar tipo datetime para evitar fallos en el merge
            df_p['fecha'] = pd.to_datetime(df_p['fecha'])

            df_merge = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].merge(
                df_p[['fecha', 'afluencia', 'zscore_robusto', 'anomalia_mad', 'es_cierre']], # <--- CONECTADO AQUÍ
                left_on='ds', right_on='fecha'
            )

            # Detecciones
            df_merge['det_prophet'] = (df_merge['afluencia'] < df_merge['yhat_lower']) | (df_merge['afluencia'] > df_merge['yhat_upper'])
            
            # Usamos DIRECTAMENTE el resultado de la MAD estacional previa
            df_merge['det_mad'] = df_merge['anomalia_mad'] # <--- USA TU PRIMER MAD SIN REEVALUAR

            # Reglas de Consenso (un cierre operativo va primero: no es anomalia de demanda)
            conditions = [
                df_merge['es_cierre'],
                (df_merge['det_prophet'] & df_merge['det_mad']),
                (df_merge['det_prophet'] & ~df_merge['det_mad']),
                (~df_merge['det_prophet'] & df_merge['det_mad'])
            ]
            prioridades = ['CIERRE (Operativo)', 'CRÍTICA (Consenso)', 'ALTA (Solo Prophet)', 'MEDIA (Solo MAD)']
            df_merge['prioridad_auditoria'] = np.select(conditions, prioridades, default='Normal')

            df_merge['linea'] = linea
            df_merge['estacion'] = estacion
            df_merge['impacto_pasajeros'] = round(df_merge['afluencia'] - df_merge['yhat'], 0)

            # --- Etiquetado de la dirección de la anomalía ---
            df_merge['direccion_anomalia'] = np.where(df_merge['impacto_pasajeros'] > 0, 'Alza (Pico atípico)', 'Baja (Caída atípica)')

            # Grafica de pronostico de la serie (un fallo al graficar no descarta las anomalias)
            if carpeta_graficas:
                try:
                    graficar_pronostico_serie(linea, estacion, df_merge, forecast_futuro, carpeta_graficas)
                except Exception as e_graf:
                    print(f"Aviso: no se pudo graficar {estacion} ({linea}): {e_graf}")

            # Guardar el pronostico de Prophet de la serie (todos los dias, con su etiqueta; futuros con es_futuro=True)
            cols_fc = ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
            serie_completa = pd.concat([
                df_merge[cols_fc + ['afluencia', 'zscore_robusto', 'prioridad_auditoria']].assign(es_futuro=False),
                forecast_futuro[cols_fc].assign(es_futuro=True)
            ], ignore_index=True)
            # Componentes de Prophet: efecto de festivos (MX), estacionalidad anual y tendencia (en pasajeros)
            serie_completa = serie_completa.merge(forecast_total[['ds', 'holidays', 'yearly', 'trend']], on='ds', how='left')
            serie_completa['linea'] = linea
            serie_completa['estacion'] = estacion
            series_prophet.append(serie_completa)
            
            # Guardar solo anomalías (los cierres operativos quedan en series_prophet, no en el master)
            anomalias = df_merge[~df_merge['prioridad_auditoria'].isin(['Normal', 'CIERRE (Operativo)'])].copy()
            resultados_master.append(anomalias)

            if i % 10 == 0: print(f"Progreso: {i}/{total} estaciones procesadas.")

        except Exception as e:
            print(f"Error en {estacion} ({linea}): {e}")
            continue

    df_final = pd.concat(resultados_master, ignore_index=True)
    df_series = pd.concat(series_prophet, ignore_index=True)
    return df_final, df_series

# Ejecución
# (deja una grafica por serie en modeling/img_pronosticos/<linea>/<estacion>.png;
#  GENERAR_GRAFICAS = False para recalcular solo los datos sin tocar las imagenes)
master_auditoria, series_prophet = motor_auditoria_consenso_mad_bidireccional(
    df_limpio, carpeta_graficas='modeling/img_pronosticos' if GENERAR_GRAFICAS else None)

master_auditoria.to_csv('master_auditoria_consenso_MAD.csv', index=False)
master_auditoria.to_excel('master_auditoria_consenso_MAD.xlsx', index=False)

# Pronosticos de Prophet de todas las series (historico + DIAS_FUTURO dias futuros): insumo del modelo de riesgo (RF/XGBoost)
os.makedirs('data/processed', exist_ok=True)
series_prophet.to_pickle('data/processed/prophet_series.pkl')
