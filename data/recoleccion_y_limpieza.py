# %%
# Recoleccion y limpieza (dataset simple + dataset desglosado).
# Fusion de los antiguos data/01_recoleccion_y_limpieza.py + data/02_carga_dataset_desglosado.py.
# Contexto y hallazgos: ver ANALISIS.md (esta misma carpeta).
# Este script es autocontenido: descarga y limpia los datos desde cero y guarda
# los checkpoints que usan eda/ y feature_engineering/ (no depende de que se
# haya corrido nada mas antes, en el mismo kernel o en otro).

import os
import pandas as pd

# %%
url = "https://datos.cdmx.gob.mx/dataset/f2046fd5-51b5-4876-b008-bd65d95f9a02/resource/0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb/download/afluenciastc_simple_02_2026.csv"
metro = pd.read_csv(url, encoding = 'utf-8', parse_dates=True) # parse es para convertir fechas

# %%
metro

# %%
metro.info()

# %%
metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime

# %%
metro.pop('mes')

# %%
def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    
    try:
        texto_limpio = texto.encode('latin-1').decode('utf-8')
    except:
        texto_limpio = texto.replace('Ã\xad', 'í')
    
    texto_limpio = texto_limpio.replace('Línea', 'Linea') # para lineas que no tengan el acento
    texto_limpio = texto_limpio.replace('linea', 'Linea')
    texto_limpio = texto_limpio.lower()
    return texto_limpio

# %%
metro['linea'] = metro['linea'].apply(limpiar_texto)

# %%
metro['estacion'] = metro['estacion'].apply(limpiar_texto)

# %%
metro['estacion'].duplicated().any()

# %%
metro['linea'].unique()

# %%
metro.isnull().sum()

# %%
metro.index

# %%
'''metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime 
metro.set_index('fecha', inplace=True)'''

# %%
type(metro.index)
# pandas.core.indexes.datetimes.DatetimeIndex si tenemos como indice la fecha

# %%
print(f"Se tiene un total de {metro['estacion'].nunique()} estaciones en todo el conjunto de datos") # nunique cuenta el numero unico de instancias

# %%
metro[metro['afluencia'] == 0].count()

# %%
#el dataset es muy grande, por lo que no se puede guardar como excel
#metro.to_excel('metro_limpio.xlsx', index= False)

# %%
# Snapshot del metro "simple" (2010-2026) antes de que se sobreescriba abajo con
# el dataset desglosado; eda/analisis_exploratorio.py usa este checkpoint para el
# primer vistazo (serie completa, incluye la caida por pandemia).
metro_simple = metro.copy()
os.makedirs('data/processed', exist_ok=True)
metro_simple.to_pickle('data/processed/metro_simple.pkl')

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
# Checkpoint: guarda dataset_original_copy para que eda/, feature_engineering/
# y modeling/ lo carguen sin tener que re-descargar y re-limpiar el CSV completo.
os.makedirs('data/processed', exist_ok=True)
dataset_original_copy.to_pickle('data/processed/dataset_original_copy.pkl')
