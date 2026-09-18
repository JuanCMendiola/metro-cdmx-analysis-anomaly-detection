# Descomposicion STL y preprocesamiento final antes del modelado.
# Extraido automaticamente de tt.ipynb, celdas [96-112] (sin modificar codigo).

# %% [markdown]
# # **PREPROCESAMIENTO**

# %% [markdown]
# ## **DESCOMPOSICIÓN DE LAS SERIES**

# %% [markdown]
# + **Descomposición clásica** *Expresa la serie (y(t)) como una combinación de 3 componentes*
#
#     **Metodos de descomposición**
#     * Descomposición aditiva: y(t) = S(t) + T(t) + R(t) -> (Cuando la magitud del componente estacional se mantiene relativamente constantea pesar de la tendencia)
#     * Descomposición multiplocativa: y(t) = S(t) * T(t) * R(t) -> (Cuando la magitud del componente estacional cambia proporcionalmente con la tendencia) **Este parece ser el caso de las series de tiempo del metro**

# %% [markdown]
# Se puede observar un compportamiento estacional semanal para cada linea, la multiplicativa no puede tener 0 o valores negativos, por el momento se tienen valores 0 en 2023 para la linea 1, asi que si se usa el año 2024 se tiene un **promedio residual** usando la multiplicativa de 0.9 para la mayoría de las lineas, pero en el caso de la aditiva en algunas presenta valores de hasta -30 muy lejanas a 0, por lo que se debe tratar los valores nulos o acortar la serie a 2024 o eliminar estaciones que presenten demasiados 0. Por el momento la **multiplicativa** arroja los mejores resultados.

# %% [markdown]
# ### **STL**

# %% [markdown]
# Se usó la descomposicón con STL porque es un metodo más robusto, porque estima la estacionalidad usando local regression la cual toma en cuenta la periodisidad de la serie, esto es importante porque las series presentan periodisidad, ademas de que puede determinar las variaciones a largo plazo, los residuos los obtiene de tomar la serie original y restarle la periodisidad.

# %% [markdown]
# Cada serie parece mostrar distintos patrones de tendencia, estacionalidad y residuales con mucha varianza por lo que no son residuales que presenten homocedasticidad, para eso se saco el promedio de los residuales y no son tan cercanos a 0 por lo que se deben aplicar mas pruebas estadisticas para definir el modelo o decidir si se harán transformaciones o diferenciaciones, pero al ser 195 series resulta complicado evaluar una por una por lo que los resultados nos encaminana a un modelo global si se quiere hacer pronósticos.

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
        plt.show()

        print(f'Promedio residuales de descomposición aditiva: {desc_STL.resid.mean()}')

# %% [markdown]
# Al siguiente dataset se llenara con NaN para hacer las primeras pruebas de modelos, aunque falten pruebas

# %%
af_dia_est['afluencia'] = af_dia_est['afluencia'].replace(0, np.nan)

# %% [markdown]
# # **PREPROCESAMIENTO PARA MODELO**

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
import os
os.makedirs('data/processed', exist_ok=True)
af_modelo.to_pickle('data/processed/af_modelo.pkl')
