# Estadisticas moviles, ACF/PACF y visualizacion de series con anomalias.
# Extraido automaticamente de tt.ipynb, celdas [71-95] (sin modificar codigo).

# %% [markdown]
# # **FEATURE ENGINEERING**

# %% [markdown]
# Estadísticas moviles son importantes para comenzar el análisis de series de tiempo ya que nos permiten identificar comportamiento en la serie en ciertas ventanas de tiempo, se tomaron en cuenta la media movil, la desviación estandar movil para cada estación,
#
# Además se tomaron en cuenta otras medidas como el cambio porcentual ya que nos servirá para la detección de cambios significativos en la series con respecto a una ventana de tiempo, por otro lado se agregó el estadístico z-score con el fin de encontrar puntos que se salen de los valores esperados, para tomar los más alejados se tomo como umbral mayores a 3 desviaciones estándar.
#
# Por lo que al combinar el cambio porcentual mayor al 85% y estadístico z-score > 3 deviaciones estándar estariamos tomando valores muy atípicos para poder clasificarlo como una anomalía en terminos estadísticos, además se tomará en cuenta un modelo que pueda captar no solo el valor alejado si no que tome en cuenta otras variables que podrían estar sesgando los estadísticos, como sería, días feriados o si la estación estuvo cerrada o es fin de semana

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

# %% [markdown]
# ## **GRÁFICA DE FUNCIÓN DE AUTOCORRELACIÓN**

# %% [markdown]
# Las siguientes gráficas nos proporcionan información valiosa, ya que nos indican que todas las series no son estacionarias, que modelos AR, MA, ARMA, pueden no capturar el comportamiento por que la series no son estables, tienen estacionalidad, alta volatilidad, por lo que se tendría que hacer un análisis para hacer transformaciones para quitar la estacionalidad y ver si es posible que la serie sea estacionaria

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
        plt.title(f'{linea} - Estación {estacion}\nPeriodo: {i} - {FECHA_FIN.year}', 
                  fontsize=18, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.9, linestyle='--')
        plt.tight_layout()
        plt.show()

# %% [markdown]
# # **Función de Autocorrelación Parcial**

# %% [markdown]
# Al igual que las otras gráficas de autocorrelación confirman que la series no son estacionarias por lo que aplicar modelos sin diferenciar o transformaciones no podrían modelar los datos.

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
        plt.title(f'{linea} - Estación {estacion}\nPeriodo: {i} - {FECHA_FIN.year}', 
                  fontsize=18, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.9, linestyle='--')
        plt.tight_layout()
        plt.show()

# %% [markdown]
# ## **VISUALIZACIÓN DE LAS SERIES DE TIEMPO CON ANOMALÍAS**

# %% [markdown]
# A continuación se observan las 195 series de tiempo, donde los puntos rojos representan cambios mayores al 85% en la serie y los puntos morados representan valores que se alejan 3 desviaciones estandar

# %% [markdown]
# Se obtuvieron los siguientes resultados tras la visualización de las series:
#
#
# Juanacatlán, tacubaya y observatorio al no tienen suficientes datos.
#
# Toda la linea 1 presenta valores 0 por que estuvo en mantenimiento.
#
# Estaciones de la linea 12 presentan 0.
#
# Linea 9: pantitlan, puebla, ciudad deportiva también presentan 0.
#
# Como se mencionó en la eliminación de variables, se dejo una escala de tiempo apartir de
# septiembre de 2023 porque para las lineas 12 y 1 se cortaba por lo que no serviría para el modelado.

# %% [markdown]
# **Estaciones con mayor número de valores atípicos:**
#
# Linea 1: candelaria, merced
#
# Linea 2: Allende, bellas artes, pino Suárez, zócalo, hidalgo
#
# Linea 4: canal del norte, candelaria, fray Servando, Morelos, santa Anita
#
# Linea 5: consulado
#
# Linea 6: la villa
#
# Linea 7: constituyentes
#
# Linea 8: apatlalco, bellas artes, Iztapalapa, la viga
#
# Linea 9: ciudad deportiva, Jamaica, velódromo, los reyes
#
# Linea b: san lazaro

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
        plt.show()

        print(round(datos_filtrados[datos_filtrados.index > FECHA_INICIO].describe(),2))

# %% [markdown]
# # **DATASET FILTRADO PARA CLASIFICACIÓN DE ANOMALÍAS**

# %%
af_dia_est['estacion_cerrada'] = (af_dia_est['afluencia'] == 0).astype(int)

# %%
af_anom = af_dia_est[(af_dia_est['anomalia_z']==True) & (af_dia_est['cambio_%']>85)]
print(af_anom)

# %% [markdown]
# ## **Excel con fechas anomalías estadísticas**

# %%
#af_anom.to_excel('anomalias_2023-2026.xlsx', index= True)
