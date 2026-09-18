# Recoleccion del dataset simple (2010-2026) e integracion/limpieza inicial.
# Extraido automaticamente de tt.ipynb, celdas [0-27] (sin modificar codigo).

# %% [markdown]
# # **LIBRERIAS**

# %%
import pandas as pd
import numpy as np
# Reinicia el kernel después de la celda de instalación y luego importa:
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.seasonal import STL
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from pmdarima import auto_arima
from prophet import Prophet
import matplotlib.ticker as ticker
from matplotlib.ticker import PercentFormatter
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error
)

# %% [markdown]
# # **RECOLECCIÓN**

# %%
url = "https://datos.cdmx.gob.mx/dataset/f2046fd5-51b5-4876-b008-bd65d95f9a02/resource/0e8ffe58-28bb-4dde-afcd-e5f5b4de4ccb/download/afluenciastc_simple_02_2026.csv"
metro = pd.read_csv(url, encoding = 'utf-8', parse_dates=True) # parse es para convertir fechas


# %%
metro

# %% [markdown]
# # **ENTENDIMIENTO DEL PROBLEMA**

# %% [markdown]
# ## ¿Existe algún patrón que nos permita predecir la afluencia de personas de manera semanal durante el periodo del año 2021 hasta la actualidad?

# %% [markdown]
# # **INTEGRACIÓN DE DATOS**

# %% [markdown]
# 1. verificar los tipos de datos que tenemos
# 2. Verificar que el indice este en formato datetame (para asegurar una serie de tiempo de pandas)
# 3. Realizar el mapeo de registros duplicados
# 4. Realizar el manejo de datos faltantes

# %%
metro.info()

# %%
metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime

# %% [markdown]
# # **LIMPIEZA**

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

# %% [markdown]
# *No hay valores faltantes pero puede haber tuplas con valor 0*

# %%
metro.index

# %%
'''metro['fecha'] = pd.to_datetime(metro['fecha']) # se le da formato datetime 
metro.set_index('fecha', inplace=True)'''

# %%
type(metro.index)
# pandas.core.indexes.datetimes.DatetimeIndex si tenemos como indice la fecha

# %% [markdown]
# Son 164 únicas pero en esta parte no se toma en cuenta que algunas líneas al estar conectadas presentan estaciones con el mismo nombre por lo que en análisis posteriores se toma en cuenta este punto y quedan un total de 195 estaciones.

# %%
print(f"Se tiene un total de {metro['estacion'].nunique()} estaciones en todo el conjunto de datos") # nunique cuenta el numero unico de instancias

# %%
metro[metro['afluencia'] == 0].count()

# %%
#el dataset es muy grande, por lo que no se puede guardar como excel
#metro.to_excel('metro_limpio.xlsx', index= False)

# %% [markdown]
# No se tienen datos faltantes, ni duplicados, pero se tiene tuplas con valores 0, puede que sea por el tipo de pago por lo que con graficos se visualizará y se tomara una decisión
