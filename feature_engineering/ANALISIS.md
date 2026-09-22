# Analisis y hallazgos - Feature engineering

Notas e interpretaciones que acompanaban a `feature_engineering.py` (antes celdas markdown en los notebooks/`.py` originales).

## Feature engineering 1/2 - Rolling stats, ACF/PACF, anomalias

# **FEATURE ENGINEERING**

Estadísticas moviles son importantes para comenzar el análisis de series de tiempo ya que nos permiten identificar comportamiento en la serie en ciertas ventanas de tiempo, se tomaron en cuenta la media movil, la desviación estandar movil para cada estación,

Además se tomaron en cuenta otras medidas como el cambio porcentual ya que nos servirá para la detección de cambios significativos en la series con respecto a una ventana de tiempo, por otro lado se agregó el estadístico z-score con el fin de encontrar puntos que se salen de los valores esperados, para tomar los más alejados se tomo como umbral mayores a 3 desviaciones estándar.

Por lo que al combinar el cambio porcentual mayor al 85% y estadístico z-score > 3 deviaciones estándar estariamos tomando valores muy atípicos para poder clasificarlo como una anomalía en terminos estadísticos, además se tomará en cuenta un modelo que pueda captar no solo el valor alejado si no que tome en cuenta otras variables que podrían estar sesgando los estadísticos, como sería, días feriados o si la estación estuvo cerrada o es fin de semana

## **GRÁFICA DE FUNCIÓN DE AUTOCORRELACIÓN**

Las siguientes gráficas nos proporcionan información valiosa, ya que nos indican que todas las series no son estacionarias, que modelos AR, MA, ARMA, pueden no capturar el comportamiento por que la series no son estables, tienen estacionalidad, alta volatilidad, por lo que se tendría que hacer un análisis para hacer transformaciones para quitar la estacionalidad y ver si es posible que la serie sea estacionaria

# **Función de Autocorrelación Parcial**

Al igual que las otras gráficas de autocorrelación confirman que la series no son estacionarias por lo que aplicar modelos sin diferenciar o transformaciones no podrían modelar los datos.

## **VISUALIZACIÓN DE LAS SERIES DE TIEMPO CON ANOMALÍAS**

A continuación se observan las 195 series de tiempo, donde los puntos rojos representan cambios mayores al 85% en la serie y los puntos morados representan valores que se alejan 3 desviaciones estandar

Se obtuvieron los siguientes resultados tras la visualización de las series:


Juanacatlán, tacubaya y observatorio al no tienen suficientes datos.

Toda la linea 1 presenta valores 0 por que estuvo en mantenimiento.

Estaciones de la linea 12 presentan 0.

Linea 9: pantitlan, puebla, ciudad deportiva también presentan 0.

Como se mencionó en la eliminación de variables, se dejo una escala de tiempo apartir de
septiembre de 2023 porque para las lineas 12 y 1 se cortaba por lo que no serviría para el modelado.

**Estaciones con mayor número de valores atípicos:**

Linea 1: candelaria, merced

Linea 2: Allende, bellas artes, pino Suárez, zócalo, hidalgo

Linea 4: canal del norte, candelaria, fray Servando, Morelos, santa Anita

Linea 5: consulado

Linea 6: la villa

Linea 7: constituyentes

Linea 8: apatlalco, bellas artes, Iztapalapa, la viga

Linea 9: ciudad deportiva, Jamaica, velódromo, los reyes

Linea b: san lazaro

# **DATASET FILTRADO PARA CLASIFICACIÓN DE ANOMALÍAS**

## **Excel con fechas anomalías estadísticas**

## Feature engineering 2/2 - STL y dataset final para modelado

# **PREPROCESAMIENTO**

## **DESCOMPOSICIÓN DE LAS SERIES**

+ **Descomposición clásica** *Expresa la serie (y(t)) como una combinación de 3 componentes*

    **Metodos de descomposición**
    * Descomposición aditiva: y(t) = S(t) + T(t) + R(t) -> (Cuando la magitud del componente estacional se mantiene relativamente constantea pesar de la tendencia)
    * Descomposición multiplocativa: y(t) = S(t) * T(t) * R(t) -> (Cuando la magitud del componente estacional cambia proporcionalmente con la tendencia) **Este parece ser el caso de las series de tiempo del metro**

Se puede observar un compportamiento estacional semanal para cada linea, la multiplicativa no puede tener 0 o valores negativos, por el momento se tienen valores 0 en 2023 para la linea 1, asi que si se usa el año 2024 se tiene un **promedio residual** usando la multiplicativa de 0.9 para la mayoría de las lineas, pero en el caso de la aditiva en algunas presenta valores de hasta -30 muy lejanas a 0, por lo que se debe tratar los valores nulos o acortar la serie a 2024 o eliminar estaciones que presenten demasiados 0. Por el momento la **multiplicativa** arroja los mejores resultados.

### **STL**

Se usó la descomposicón con STL porque es un metodo más robusto, porque estima la estacionalidad usando local regression la cual toma en cuenta la periodisidad de la serie, esto es importante porque las series presentan periodisidad, ademas de que puede determinar las variaciones a largo plazo, los residuos los obtiene de tomar la serie original y restarle la periodisidad.

Cada serie parece mostrar distintos patrones de tendencia, estacionalidad y residuales con mucha varianza por lo que no son residuales que presenten homocedasticidad, para eso se saco el promedio de los residuales y no son tan cercanos a 0 por lo que se deben aplicar mas pruebas estadisticas para definir el modelo o decidir si se harán transformaciones o diferenciaciones, pero al ser 195 series resulta complicado evaluar una por una por lo que los resultados nos encaminana a un modelo global si se quiere hacer pronósticos.

Al siguiente dataset se llenara con NaN para hacer las primeras pruebas de modelos, aunque falten pruebas

# **PREPROCESAMIENTO PARA MODELO**
