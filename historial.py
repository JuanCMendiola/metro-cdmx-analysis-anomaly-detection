# Historial de ejecuciones del pipeline.
#
# Cada script sigue escribiendo sus salidas en la misma ruta de siempre (el
# notebook y el tablero las leen de ahi). Al terminar llama a
# registrar_corrida(), que guarda una copia de esas salidas en una carpeta con
# la fecha y hora de la corrida, junto con un manifiesto: commit del codigo,
# parametros, metricas clave y huella (sha256) de cada archivo. Asi una
# corrida nueva ya no borra la anterior.
#
#   historico/<etapa>/<AAAA-MM-DD_HHMMSS>/   se sube a git: manifiesto.json y
#                                            las salidas chicas (tablas, propuesta, muestra)
#   historico_local/<etapa>/<AAAA-MM-DD_HHMMSS>/
#                                            NO se sube (.gitignore): copias pesadas
#                                            (master, pickles, parquet de series, graficas)
#   historico/registro_corridas.csv          una fila por corrida, para compararlas
#
# Si la corrida produce exactamente los mismos archivos que la anterior de esa
# etapa, no se copian otra vez: solo se anota en el registro con "igual_a".
# Para una prueba rapida sin guardar historial: SIN_HISTORIAL=1 python <script>
#
# Uso (desde la raiz del repo):
#   from historial import registrar_corrida
#   registrar_corrida('deteccion', archivos_locales=['master_auditoria_consenso_MAD.csv'],
#                     metricas={'criticas': 8575}, parametros={'umbral_z': 3.5})

import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
from zoneinfo import ZoneInfo

HISTORICO = 'historico'
HISTORICO_LOCAL = 'historico_local'
REGISTRO = f'{HISTORICO}/registro_corridas.csv'
LIMITE_MB_GIT = 5          # un archivo mas grande va a historico_local aunque se pida en `archivos`
ZONA = ZoneInfo('America/Mexico_City')
COMPRIMIR = ('.csv', '.json', '.txt', '.pkl')   # en historico_local se guardan como .gz

COLUMNAS_REGISTRO = ['id', 'etapa', 'fecha_hora', 'commit', 'codigo_sin_commit',
                     'archivos', 'igual_a', 'metricas', 'nota']


def _git(*args):
    try:
        return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def _a_json(valor):
    # numpy, pandas y fechas -> tipos que json entiende
    if hasattr(valor, 'item') and not isinstance(valor, (list, dict)):
        try:
            return valor.item()
        except (ValueError, AttributeError):
            pass
    if hasattr(valor, 'to_dict'):
        return valor.to_dict()
    if hasattr(valor, 'isoformat'):
        return valor.isoformat()
    return str(valor)


def _ultima_corrida(etapa):
    # Manifiesto de la ultima corrida de la etapa que si guardo archivos
    carpeta = f'{HISTORICO}/{etapa}'
    if not os.path.isdir(carpeta):
        return None
    for nombre in sorted(os.listdir(carpeta), reverse=True):
        ruta = f'{carpeta}/{nombre}/manifiesto.json'
        if os.path.exists(ruta):
            with open(ruta, encoding='utf-8') as f:
                return json.load(f)
    return None


def _copiar(origen, destino, comprimir):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if comprimir:
        destino += '.gz'
        with open(origen, 'rb') as fi, gzip.open(destino, 'wb', compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
    else:
        shutil.copy2(origen, destino)
    return destino


def registrar_corrida(etapa, archivos=(), archivos_locales=(), metricas=None, parametros=None, nota=''):
    """Guarda una copia de las salidas de esta corrida y su manifiesto.

    etapa:            nombre corto de la etapa ('datos', 'deteccion', 'modelo_riesgo', ...)
    archivos:         salidas chicas que se guardan en historico/ (se suben a git)
    archivos_locales: salidas pesadas que se guardan en historico_local/ (no se suben)
    metricas:         numeros clave de la corrida (conteos, errores, tasas)
    parametros:       configuracion usada (umbrales, semillas, horizonte)
    Devuelve el id de la corrida (AAAA-MM-DD_HHMMSS) o None si SIN_HISTORIAL esta activo.
    """
    if os.environ.get('SIN_HISTORIAL'):
        print(f'[historial] SIN_HISTORIAL activo: no se guardo la corrida de {etapa}.')
        return None

    ahora = dt.datetime.now(ZONA)
    id_corrida = ahora.strftime('%Y-%m-%d_%H%M%S')

    # Archivos: huella y destino (git o local)
    detalle = []
    for ruta, local in [(r, False) for r in archivos] + [(r, True) for r in archivos_locales]:
        if not os.path.exists(ruta):
            print(f'[historial] Aviso: {ruta} no existe, no se guarda.')
            continue
        mb = os.path.getsize(ruta) / 1e6
        detalle.append({'ruta': ruta.replace(os.sep, '/'), 'bytes': os.path.getsize(ruta),
                        'sha256': _sha256(ruta), 'local': local or mb > LIMITE_MB_GIT})

    # Codigo: commit y si habia cambios sin commit en scripts o notebooks
    cambios = [l[3:] for l in _git('status', '--porcelain').splitlines()
               if l[3:].endswith(('.py', '.ipynb'))]
    manifiesto = {
        'id': id_corrida,
        'etapa': etapa,
        'fecha_hora': ahora.isoformat(timespec='seconds'),
        'commit': _git('rev-parse', '--short', 'HEAD'),
        'rama': _git('rev-parse', '--abbrev-ref', 'HEAD'),
        'codigo_sin_commit': cambios,
        'python': platform.python_version(),
        'parametros': parametros or {},
        'metricas': metricas or {},
        'nota': nota,
        'archivos': detalle,
    }

    # Si los archivos son identicos a la ultima corrida de la etapa, no se copian de nuevo
    previa = _ultima_corrida(etapa)
    igual_a = ''
    if previa and detalle and (sorted((a['ruta'], a['sha256']) for a in detalle)
                               == sorted((a['ruta'], a['sha256']) for a in previa.get('archivos', []))):
        igual_a = previa['id']
    else:
        for a in detalle:
            raiz = HISTORICO_LOCAL if a['local'] else HISTORICO
            comprimir = a['local'] and a['ruta'].endswith(COMPRIMIR)
            a['copia'] = _copiar(a['ruta'], f"{raiz}/{etapa}/{id_corrida}/{a['ruta']}", comprimir).replace(os.sep, '/')
        os.makedirs(f'{HISTORICO}/{etapa}/{id_corrida}', exist_ok=True)
        with open(f'{HISTORICO}/{etapa}/{id_corrida}/manifiesto.json', 'w', encoding='utf-8') as f:
            json.dump(manifiesto, f, ensure_ascii=False, indent=2, default=_a_json)

    # Registro: una fila por corrida (tambien las que no cambiaron nada)
    nuevo = not os.path.exists(REGISTRO)
    os.makedirs(HISTORICO, exist_ok=True)
    with open(REGISTRO, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_REGISTRO)
        if nuevo:
            w.writeheader()
        w.writerow({
            'id': id_corrida, 'etapa': etapa, 'fecha_hora': manifiesto['fecha_hora'],
            'commit': manifiesto['commit'], 'codigo_sin_commit': ' '.join(cambios),
            'archivos': len(detalle), 'igual_a': igual_a,
            'metricas': json.dumps(metricas or {}, ensure_ascii=False, default=_a_json), 'nota': nota,
        })

    if igual_a:
        print(f'[historial] {etapa}: mismas salidas que la corrida {igual_a}; solo se anoto en {REGISTRO}.')
    else:
        print(f'[historial] {etapa}: corrida {id_corrida} guardada en {HISTORICO}/{etapa}/{id_corrida}/'
              + (f' (copias pesadas en {HISTORICO_LOCAL}/)' if any(a['local'] for a in detalle) else ''))
    if cambios:
        print(f'[historial] Aviso: habia cambios sin commit en {", ".join(cambios)}; '
              'el commit del manifiesto no basta para reproducir esta corrida.')
    return id_corrida
