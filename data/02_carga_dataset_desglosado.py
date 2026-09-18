# Carga y limpieza del dataset desglosado (linea/estacion/tipo_pago).
# Extraido automaticamente de tt.ipynb, celdas [34-36] (sin modificar codigo).

# %% [markdown]
# # **LIMPIEZA-METRO-NUEVO-DATASET-DESGLOSADO**

# %% [markdown]
# Se repite el preprocesamiento para el nuevo dataset desglosado que contiene los datos de semovi a partir del 2021 y se consituyen los datos a usar a partir de enero del 2022

# %%
url = "https://datos.cdmx.gob.mx/dataset/f2046fd5-51b5-4876-b008-bd65d95f9a02/resource/cce544e1-dc6b-42b4-bc27-0d8e6eb3ed72/download/afluenciastc_desglosado_02_2026.csv"
metro = pd.read_csv(url, encoding = 'utf-8', parse_dates=True) # parse es para convertir fechas
metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime

#Filtrado para obtener solo los años 2022 - 2026
metro = metro[metro['fecha'] >= '2022-01-01'].copy()
metro.pop('mes')
metro['linea'] = metro['linea'].apply(limpiar_texto)
metro['estacion'] = metro['estacion'].apply(limpiar_texto)
metro['estacion'].duplicated().any()
metro['linea'].unique()
metro.isnull().sum()
metro.index
'''metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime 
metro.set_index('fecha', inplace=True)'''
type(metro.index)
print(f"Se tiene un total de {metro['estacion'].nunique()} estaciones en todo el conjunto de datos") # nunique cuenta el numero unico de instancias
metro[metro['afluencia'] == 0].count()

#Realizar copia del dataset original para uso en el modelado
dataset_original_copy = metro.copy()

# %%
# Checkpoint: guarda dataset_original_copy para que modeling/ lo cargue sin
# tener que re-descargar y re-limpiar el CSV completo.
import os
os.makedirs('data/processed', exist_ok=True)
dataset_original_copy.to_pickle('data/processed/dataset_original_copy.pkl')
