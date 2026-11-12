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
constante `ARCGIS_URL` al inicio de `dashboard/app.py`.
Así lo ve cualquier visitante. Alternativa sin tocar código, en Settings → Secrets:

```toml
arcgis_url = "https://www.arcgis.com/apps/mapviewer/index.html?webmap=..."
```

## Pestañas

Pensado para usuarios, con dos pestañas:

- **Mapa:** el mapa web de ArcGIS Online del equipo (constante `ARCGIS_URL`) y, a
  la derecha, el ranking de estaciones con más afluencia o más anomalías en el
  periodo elegido (las anomalías leves se pueden incluir con un interruptor).
- **Series de tiempo:** se elige línea y estación en listas desplegables; muestra
  afluencia real, rango normal de Prophet, pronóstico y anomalías marcadas, con la
  causa encontrada en la investigación OSINT cuando existe.

## Siguientes pasos

- Cada vez que se actualicen los datos de SEMOVI o se reentrene el modelo, volver a
  correr `python dashboard/preparar_datos.py` y subir `dashboard/data/`.
