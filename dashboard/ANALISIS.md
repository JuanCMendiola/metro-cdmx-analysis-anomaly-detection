# Dashboard - notas y limitaciones

Prototipo inicial (Streamlit) para visualizar en un mapa la demanda total y
las anomalías detectadas por `modeling/modelado.ipynb`, por línea/estación.

## Fuente de las coordenadas (`estaciones_coordenadas.csv`)

El dataset de afluencia (`datos.cdmx.gob.mx`) no incluye latitud/longitud de
las estaciones. El portal de datos abiertos de la CDMX sí publica un dataset
oficial de líneas y estaciones con geometría ("Líneas y Estaciones del STC
Metro (SHP)"), pero no fue accesible desde este entorno al momento de armar
el prototipo.

En su lugar, las coordenadas de `estaciones_coordenadas.csv` se extrajeron de
un mapa Folium (`mapa_estaciones.html`) publicado en un repositorio público
de terceros en GitHub
([MarcosIsaacRodriguezMoreno/Proyecto-Final-Modulo-6](https://github.com/MarcosIsaacRodriguezMoreno/Proyecto-Final-Modulo-6)),
que a su vez las calcula promediando puntos GTFS por estación. Se
normalizaron los nombres de línea/estación con la misma función
`limpiar_texto` que usa el resto del pipeline, para poder cruzarlas por
(`linea`, `estacion`) contra `master_auditoria_consenso_MAD.csv` /
`af_modelo.pkl`. Cobertura verificada: **196/196** combinaciones
línea-estación del dataset del proyecto tienen coordenada (dos filas,
`linea 1` / `gómez farias` y `gómez farías`, corresponden a la misma
estación física con dos grafías distintas en la fuente original — ambas
quedaron con la misma coordenada).

**Pendiente / a verificar:** esta fuente es de terceros, no la oficial. Antes
de usar el dashboard para algo mas que un prototipo, conviene:
1. Conseguir el dataset oficial de `datos.cdmx.gob.mx` ("Líneas y Estaciones
   del STC Metro") y revalidar/reemplazar estas coordenadas contra él.
2. Revisar visualmente en el mapa que ninguna estación quedó mal ubicada.

## Qué necesita el dashboard para correr

El dashboard solo lee archivos que están en el repo, así que se puede desplegar
tal cual:

- `dashboard/data/series_estaciones.parquet`, `riesgo_top_estaciones.parquet` y
  `riesgo_dias_alerta.parquet`: los genera `python dashboard/preparar_datos.py`
  a partir de `data/processed/prophet_series.pkl` (de `modeling/prophet_mad.py`)
  y de `propuesta_anomalias_futuras.csv/.xlsx` (de `modeling/modelado.ipynb`).
  Hay que volver a correrlo cada vez que se actualicen el detector o el modelo.
- `bitacora_investigacion_anomalias_criticas.csv` (investigación OSINT).
- `dashboard/estaciones_coordenadas.csv`.

Correr local: `streamlit run dashboard/app.py` (desde la raíz del repo). El tema
gris/naranja está en `.streamlit/config.toml`.

Desplegar: en Streamlit Community Cloud (share.streamlit.io) → New app → este
repo, rama `main`, archivo `dashboard/app.py`.

Mapa de ArcGIS Online: compartirlo como **público** y poner su enlace en la
constante `ARCGIS_URL` al inicio de `dashboard/app.py` (opcional: `ARCGIS_CAPA`
con una capa `.../FeatureServer/0` para dibujarla sobre el mapa del dashboard).
Así lo ve cualquier visitante. Alternativa sin tocar código, en Settings → Secrets:

```toml
arcgis_url = "https://www.arcgis.com/apps/mapviewer/index.html?webmap=..."
arcgis_capa = "https://services.arcgis.com/.../FeatureServer/0"   # opcional
```

## Pestañas

- **Resumen:** indicadores, anomalías por mes, por línea y calendario mes/año.
- **Mapa:** calor, columnas 3D o puntos con el color de cada línea (pydeck,
  fondo Carto sin token); indicador de anomalías, afluencia o impacto.
- **Estación:** afluencia real, banda esperada y pronóstico de Prophet con las
  anomalías marcadas, más sus registros OSINT.
- **Riesgo próximo:** top de estaciones del modelo XGBoost + Prophet, fechas con
  más estaciones en alerta y calendario de alertas.
- **Causas (OSINT):** causas, severidad, matriz de vulnerabilidad y
  estacionalidad de la bitácora.
- **ArcGIS:** muestra el mapa web o dashboard de ArcGIS Online configurado en
  `ARCGIS_URL`.

## Siguientes pasos

- Reemplazar las coordenadas por la fuente oficial de la CDMX (se puede poner
  la capa oficial en `ARCGIS_CAPA` para compararlas sobre el mapa).
- Dibujar la red como líneas, no solo estaciones.
