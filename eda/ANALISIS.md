# Analisis y hallazgos - EDA

Notas e interpretaciones que acompanaban a `analisis_exploratorio.py` (antes celdas markdown en los notebooks/`.py` originales). Las graficas referidas se generan en `img/` al correr el script.

## EDA 1/2 - Dataset simple (2010-2026)

# **EDA-METRO-SIMPLE-2010-2026**

- estadística descriptiva
- herramientas gráficas
- creatividad
El análisis exploratorio siempre debe ir acompañado de una pregunta que queramos responder y todo lo que se haga en el análisis debe ser orientado a responder esa pregunta.

En esta primer serie de tiempo, explica la afluencia diaria del metro de manera general en todas las estaciones, sin tener el nivel de detalle de la linea o estación, es un primer vistazo a la serie de tiempo general diaria de todo el metro de la CDMX.

*A simple vista se observan patrones de tendencia creciente y ciertos patrones de estacionalidad anual pero sobre todo se nota una diferencia notoria en los datos divididos por la temporada de pandemia, se decidio trabajar con los datos postpandemia a partir de aqui, ya que representan 4 años de datos y aumentando hasta la actualidad (enero 2025)*

## EDA 2/2 - Dataset desglosado (2022-2026)

# **EDA-METRO-NUEVO-DATASET-DESGLOSADO**

- estadística descriptiva
- herramientas gráficas
- creatividad
El análisis exploratorio siempre debe ir acompañado de una pregunta que queramos responder y todo lo que se haga en el análisis debe ser orientado a responder esa pregunta.

En esta agrupacción igual se muestra un análisis general pero tomando en cuenta post-pandemia, que será graficado más adelante, porque como se mencionó los patrones de afluencia cambiaron después de la pandemia

Dataset que servirá más adelante para un análisis más particular donde se tome en cuenta las estaciones y a que línea pertenece

Se observa la serie de tiempo que se ha cortado post-pandemia donde se observa el comportamiento esperado de recuperación de los niveles de afluencia conforme pasa cada año.

Sin tomar en cuenta el año 2026, En el siguiente gráfico se nota con mayor precisión el aumento de la afluencia por año, creciendo aproximadamente 1% cada año, entonces se espera cierta tendencia en las series de tiempo

Analizamos la afluencia sumada del periodo de años analizados (2022-2026) pero por línea del metro, para conocer las líneas mas afluenciadas en el periodo completo analizado

El gráfico muestra el siguiente top de lineas mas afluenciadas
1. Línea 2 (17.5%)
2. Línea 3 (14.9%)
3. Línea b (10.9%)
4. Línea 8 (10.6%)
5. Línea 1 (8.2%)

A continuación se desglosa la afluencia total del periodo 2022-2026 en función de cada línea dividido por estación correspondiente a dicha línea.

De esta gráfica podemos notar el siguiente top de estaciones mas afluenciadas por línea:

1. Línea 1:
    1. Chapultepec
    2. Merced
    3. Insurgentes
    4. Pantitlán
2. Línea 2:
    1. Cuatro caminos
    2. Tasqueña
    3. Zocalo / Tenochtitlan
3. Línea 3:
    1. Indios Verdes
    2. Universidad
    3. Copilco
4. Línea 4:
    1. Martin Carrera
    2. Candelaria
    3. Fray Servando
5. Línea 5:
    1. Pantitlán
    2. Politecnico
    3. Autobuses del norte
    4. Puerto áereo
6. Línea 6:
    1. Martin carrera
    2. Ferreria / Arena CDMX
    3. Lindavista
    4. El rosario
7. Línea 7:
    1. Barranca del Muerto
    2. Polanco
    3. Audítorio
    4. El rosario
8. Línea 8
    1. Constitución de 1917
    2. San Juan de Letrán
    3. Coyuya
    4. UAM
9. Línea 9:
    1. Tacubaya
    2. Pantitlán
    3. Chilpancingo
10. Línea a:
    1. La paz
    2. Santa Marta
    3. Pantitlán
11. Línea b:
    1. Buenavista
    2. Ciudad Azteca
    3. Mezquis
12. Línea 12:
    1. Tlahuac
    2. Periferico Oriente
    3. Insurgentes Sur

En el gráfico de afluencia por tipo de pago podemos ver como practicamente en el 2025 desapareció la modalidad del boleto en toda la red del metro, por lo que esta información no es reelevante para modelos de series de tiempo porque es indiferente el metodo usado para transladarse ya que lo que nos importa es la afluencia

De la siguiente gráfica de distribución de la afluencia acumulada del 2022-2026 podemos notar lo siguiente:
Los outliers superiores (los puntos que llegan a los 30M) no son errores; son las estaciones "ancla" del sistema (como Pantitlán, Indios Verdes o Cuatro Caminos).

Podemos notar que la red del Metro es altamente dependiente de menos del 5% de sus estaciones. Si una de estas estaciones de "30 millones" falla, el impacto sistémico es masivo, a diferencia de las estaciones que están dentro de la "caja" (el promedio).

El siguiente gráfico de distribución diaria por línea muestra el comportamiento diario normal de la afluencia en cada una de las líneas del sistema del metro, esto nos será muy relevante mas adelante

## Mapa de calor

El siguiente mapa de calor se realizó con la intención de ver meses más afluenciados y se nota que octubre y noviembre son unos de los meses con mayor afluencia, especialmente en 2025 se nota el crecimiento en la alfuencia

*La matriz de correlación muestran poca correlación si acaso se nota un pequeño grado de correlación entre pares de años consecutivos y esto es por la tendencia que va incrementando cada año*

La siguiente gráfica muestra el top 10 promedio diario de afluencia por estaciones de cada línea, debemos tener en cuenta que está contemplado por cada estación perteneciente a una línea, no es el promedio acumulado de una sola estación que tiene transbordes y pertenece a diferentes líneas. Se toma individualmente estación que pertenece a una línea.

La siguiente serie de tiempo muestra la afluencia total por linea del periodo 2022-2026. A partir de la misma pudimos notar lo siguiente:
1. Obras de Infraestructura (Líneas 1 y 12)

    Línea 12 (Naranja): Se observa claramente el periodo de inactividad total en 2022 (línea en cero). A partir de inicios de 2023, se ven "escalones" de subida que corresponden a las reaperturas por tramos.

    Línea 1 (Rosa): se nota la caída drástica a mediados de 2022. Esto marca el inicio del proyecto de mantenimiento. La fluctuación posterior refleja la operación parcial y el desvío de usuarios a otras rutas.

2. Estacionalidad Marcada
    Se observa que el final de cada año (diciembre-enero), todas las líneas presentan una "V" o caída pronunciada.

    Interpretación: Es el efecto de las vacaciones de invierno y la suspensión de actividades escolares/administrativas.

3. Líneas más relevantes (Líneas 2 y 3)
    Las líneas 2 y 3 se mantienen consistentemente en la cima, rozando los 17.5M a 20M de pasajeros mensuales.

4. Líneas Estables (Líneas 4 y 6)
    Las líneas en la parte inferior de la gráfica muestran una estabilidad casi plana.
