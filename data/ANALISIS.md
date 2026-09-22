# Analisis y hallazgos - Recoleccion y limpieza

Notas e interpretaciones que acompanaban a `recoleccion_y_limpieza.py` (antes celdas markdown en los notebooks/`.py` originales).

## Datos 1/2 - Recoleccion y limpieza (dataset simple)

# **LIBRERIAS**

# **RECOLECCIÓN**

# **ENTENDIMIENTO DEL PROBLEMA**

## ¿Existe algún patrón que nos permita predecir la afluencia de personas de manera semanal durante el periodo del año 2021 hasta la actualidad?

# **INTEGRACIÓN DE DATOS**

1. verificar los tipos de datos que tenemos
2. Verificar que el indice este en formato datetame (para asegurar una serie de tiempo de pandas)
3. Realizar el mapeo de registros duplicados
4. Realizar el manejo de datos faltantes

# **LIMPIEZA**

*No hay valores faltantes pero puede haber tuplas con valor 0*

Son 164 únicas pero en esta parte no se toma en cuenta que algunas líneas al estar conectadas presentan estaciones con el mismo nombre por lo que en análisis posteriores se toma en cuenta este punto y quedan un total de 195 estaciones.

No se tienen datos faltantes, ni duplicados, pero se tiene tuplas con valores 0, puede que sea por el tipo de pago por lo que con graficos se visualizará y se tomara una decisión

## Datos 2/2 - Carga y limpieza (dataset desglosado)

# **LIMPIEZA-METRO-NUEVO-DATASET-DESGLOSADO**

Se repite el preprocesamiento para el nuevo dataset desglosado que contiene los datos de semovi a partir del 2021 y se consituyen los datos a usar a partir de enero del 2022
