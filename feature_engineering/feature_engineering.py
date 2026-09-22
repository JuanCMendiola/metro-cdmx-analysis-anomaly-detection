# %%
# Rolling stats, ACF/PACF, deteccion visual de anomalias, descomposicion STL
# y dataset final para modelado.
# Fusion de los antiguos feature_engineering/01_feature_engineering.py +
# feature_engineering/02_preprocesamiento.py.
# Contexto y hallazgos: ver ANALISIS.md (esta misma carpeta).
# Cada grafica se guarda en feature_engineering/img/ (plt.savefig), igual que
# en eda/analisis_exploratorio.py. El backend 'Agg' hace que plt.show() no
# abra ninguna ventana ni bloquee la ejecucion al correr esto como script.
# Este script es autocontenido: carga el checkpoint que genera
# eda/analisis_exploratorio.py (no depende de que se haya corrido en el mismo
# kernel; solo de que ese checkpoint ya exista en disco).

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import statsmodels.api as sm
from statsmodels.tsa.seasonal import STL

os.makedirs('feature_engineering/img', exist_ok=True)

af_dia_est = pd.read_pickle('data/processed/af_dia_est.pkl')

# %%
agg = af_dia_est.sort_values('fecha').groupby(['linea', 'estacion'])['afluencia'] # solo columna afluencia agrupada por linea y estacion

af_dia_est['media_movil'] = round((agg.rolling(window=60, min_periods=1).mean().reset_index(level=[0,1], drop=True)),2) # reset porque rolling + group by agrega dos columnas al indice
af_dia_est['std_movil'] = round((agg.rolling(window=60, min_periods=1).std().reset_index(level=[0,1], drop=True)),2)
af_dia_est['cambio_%'] = round(100*abs((af_dia_est['afluencia']-af_dia_est['media_movil'])/af_dia_est['media_movil']),2)

af_dia_est['zscore_movil'] = (
    af_dia_est['afluencia'].values - af_dia_est['media_movil'].values
) / af_dia_est['std_movil'].values

af_dia_est['anomalia_z'] = abs(af_dia_est['zscore_movil']) > 3
af_dia_est

# %%
# Definir los límites fijos
FECHA_INICIO = pd.Timestamp('2023-09-01')
FECHA_FIN = pd.Timestamp('2026-01-01')

# %%
af_dia_est=af_dia_est[af_dia_est['fecha']>f'{FECHA_INICIO}']
af_dia_est = af_dia_est.copy()
af_dia_est['fecha'] = pd.to_datetime(af_dia_est['fecha'])
af_dia_est.set_index('fecha', inplace=True)

# %%
af_dia_est.info()

# %%
#af_dia_est.to_excel('metro_2024-2025.xlsx', index= False)

# %%
#af_dia_est['media_movil'] = (af_dia_est.sort_values('fecha').groupby(['linea', 'estacion'])['afluencia']
#                             .rolling(window=365, min_periods=1).mean().reset_index(level=[0,1], drop=True))
#af_dia_est

# %%
lineas_unicas = af_dia_est['linea'].unique()

for linea in lineas_unicas[:1]:
    datos_linea = af_dia_est[af_dia_est['linea'] == linea]
    estaciones_en_linea = datos_linea['estacion'].unique()
    
    for estacion in estaciones_en_linea[:1]:  
        datos_filtrados = datos_linea[datos_linea['estacion'] == estacion].sort_values('fecha')
        
        fig, ax = plt.subplots(figsize=(30, 8))
        
        sm.graphics.tsa.plot_acf(datos_filtrados['afluencia'].dropna(), lags=60, ax=ax, color = '#ff6b35')
        # lag 365 compara 2025-2024, 730 compara 2025-2023, 1095: 2025-2022

        ax.set_xlabel('Rezagos (días)')
        ax.set_ylabel('Autocorrelación')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=12)
        plt.title(f'{linea} - Estación {estacion}\nPeriodo: {FECHA_INICIO.year} - {FECHA_FIN.year}', 
                  fontsize=18, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.9, linestyle='--')
        plt.tight_layout()
        plt.savefig(f'feature_engineering/img/01_acf_{linea.replace(" ", "_")}_{estacion.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        plt.show()
        plt.close()

# %%
lineas_unicas = af_dia_est['linea'].unique()

for linea in lineas_unicas[:1]:
    datos_linea = af_dia_est[af_dia_est['linea'] == linea]
    estaciones_en_linea = datos_linea['estacion'].unique()

    for estacion in estaciones_en_linea[:1]:
        datos_filtrados = datos_linea[datos_linea['estacion'] == estacion].sort_values('fecha')

        fig, ax = plt.subplots(figsize=(30, 8))

        sm.graphics.tsa.plot_pacf(datos_filtrados['afluencia'].dropna(), lags=60, ax=ax, color = '#ff6b35', method='ywm')
        # lag 365 compara 2025-2024, 730 compara 2025-2023, 1095: 2025-2022

        ax.set_xlabel('Rezagos (días)')
        ax.set_ylabel('Autocorrelación')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=12)
        plt.title(f'{linea} - Estación {estacion}\nPeriodo: {FECHA_INICIO.year} - {FECHA_FIN.year}',
                  fontsize=18, fontweight='bold', pad=20)

        ax.grid(True, alpha=0.9, linestyle='--')
        plt.tight_layout()
        plt.savefig(f'feature_engineering/img/02_pacf_{linea.replace(" ", "_")}_{estacion.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        plt.show()
        plt.close()

# %%
n = 0
lineas_unicas = af_dia_est['linea'].unique()

for linea in lineas_unicas[:1]:
    datos_linea = af_dia_est[af_dia_est['linea'] == linea]
    estaciones_en_linea = datos_linea['estacion'].unique()
    
    for estacion in estaciones_en_linea[:1]:  # Hasta 14 estaciones por linea
        n = n+1
        datos_filtrados = datos_linea[datos_linea['estacion'] == estacion].sort_index()        
        if len(datos_filtrados) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(30, 8))
        
        sns.lineplot(data=datos_filtrados,
                     x=datos_filtrados.index,
                     y='afluencia',
                     ax=ax,
                     linewidth=2,
                     color='#0984e3')
        
        sns.lineplot(data=datos_filtrados,
                    x=datos_filtrados.index,
                    y='media_movil',
                    ax=ax,
                    linewidth=4,
                    color='#ff7f0e',
                    label = 'Media movil por año')
        
        sns.lineplot(data=datos_filtrados,
                     x = datos_filtrados.index,
                     y = 'std_movil',
                     ax=ax,
                     linewidth= 4,
                     color = 'green',
                     label = 'Std movil por año')
        
        sns.scatterplot(data=datos_filtrados[datos_filtrados['anomalia_z']],
                x=datos_filtrados[datos_filtrados['anomalia_z']].index,
                y='afluencia',
                color='black',
                label='Anomalia Z-score',
                s=400,
                )
        
        sns.scatterplot(data=datos_filtrados[datos_filtrados['cambio_%'] > 85],
                x=datos_filtrados[datos_filtrados['cambio_%'] > 85].index,
                y='afluencia',
                color='r',
                label='Cambio % > 85%',
                s=100)

        ax.set_xlim(FECHA_INICIO, FECHA_FIN)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))

        for year in range(FECHA_INICIO.year, FECHA_FIN.year + 1):
            ax.axvline(pd.Timestamp(f'{year}-01-01'),
                       color='black',
                       linestyle='-',
                       linewidth=1.5)

        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=12)

        plt.title(f'{linea} - Estación: {estacion} {n}\n'
                  f'Periodo: {FECHA_INICIO.year} - {FECHA_FIN.year}',
                  fontsize=18,
                  fontweight='bold',
                  pad=20)

        ax.grid(True, alpha=0.9, linestyle='--')
        plt.tight_layout()
        plt.savefig(f'feature_engineering/img/03_anomalias_{linea.replace(" ", "_")}_{estacion.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        plt.show()
        plt.close()

        print(round(datos_filtrados[datos_filtrados.index > FECHA_INICIO].describe(),2))

# %%
af_dia_est['estacion_cerrada'] = (af_dia_est['afluencia'] == 0).astype(int)

# %%
af_anom = af_dia_est[(af_dia_est['anomalia_z']==True) & (af_dia_est['cambio_%']>85)]
print(af_anom)

# %%
#af_anom.to_excel('anomalias_2023-2026.xlsx', index= True)

# %%
lineas_unicas = af_dia_est['linea'].unique()

for linea in lineas_unicas[:1]:
    datos_linea = af_dia_est[af_dia_est['linea'] == linea]
    estaciones_en_linea = datos_linea['estacion'].unique()
    
    for estacion in estaciones_en_linea[:1]:
        datos_filtrados = (datos_linea[datos_linea['estacion'] == estacion].sort_index())
        
        if datos_filtrados.empty:
            continue
        
        desc_STL = STL(datos_filtrados['afluencia']).fit()
        
        fig, ax = plt.subplots(4,1, figsize=(15,8), sharex=True)

        ax[0].plot(datos_filtrados.index, datos_filtrados['afluencia'], color='#1f77b4')
        ax[0].set_title('Serie Original')

        ax[1].plot(datos_filtrados.index, desc_STL.trend, color='#ff7f0e')
        ax[1].set_title('Tendencia')

        ax[2].plot(datos_filtrados.index, desc_STL.seasonal, color='#2ca02c')
        ax[2].set_title('Estacionalidad')

        ax[3].plot(datos_filtrados.index, desc_STL.resid, color='#d62728')
        ax[3].set_title('Residuales')

        plt.suptitle(f'{linea} - Estación: {estacion}\n'
                     f'Periodo: {FECHA_INICIO.year} - {FECHA_FIN.year}\n'
                     'Metodo STL',
                     fontsize=18,
                     fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'feature_engineering/img/04_stl_{linea.replace(" ", "_")}_{estacion.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        plt.show()
        plt.close()

        print(f'Promedio residuales de descomposición aditiva: {desc_STL.resid.mean()}')

# %%
af_dia_est['afluencia'] = af_dia_est['afluencia'].replace(0, np.nan)

# %%
faltantes = af_dia_est.groupby(['linea','estacion'])['afluencia'].apply(lambda x: x.isna().sum())

# %%
print(faltantes.sort_values(ascending=False))

# %%
min_obs = 500

conteo_validos = af_dia_est.groupby(['linea','estacion'])['afluencia'].count()

estaciones_validas = conteo_validos[conteo_validos >= min_obs].index

# %%
af_modelo = af_dia_est.set_index(['linea','estacion'], append=True)

af_modelo = af_modelo.loc[
    af_modelo.index.droplevel(0).isin(estaciones_validas)
]

af_modelo = af_modelo.reset_index(['linea','estacion'])

# %%
len(estaciones_validas)

# %%
af_modelo

# %%
# Checkpoint: guarda af_modelo para que modeling/ lo cargue directo, sin
# tener que re-ejecutar recoleccion, limpieza, EDA y feature engineering.
os.makedirs('data/processed', exist_ok=True)
af_modelo.to_pickle('data/processed/af_modelo.pkl')
