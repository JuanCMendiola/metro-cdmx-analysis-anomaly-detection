# Orquestador: corre data/recoleccion_y_limpieza.py, eda/analisis_exploratorio.py
# feature_engineering/feature_engineering.py y modeling/prophet_mad.py en orden, cada uno como proceso
# independiente, para dejar listos los checkpoints (data/processed/*.pkl) y las
# graficas que necesita modeling/modelado.ipynb. Pensado para correr una sola
# vez despues de clonar el repo (o cuando quieras regenerar todo desde cero).
#
# Correr con la raiz del repo como working directory:
#   python setup_pipeline.py

import subprocess
import sys

PASOS = [
    ("1/4", "data/recoleccion_y_limpieza.py"),
    ("2/4", "eda/analisis_exploratorio.py"),
    ("3/4", "feature_engineering/feature_engineering.py"),
    ("4/4", "modeling/prophet_mad.py"),
]

for numero, script in PASOS:
    print(f"\n{'='*60}\nPaso {numero}: {script}\n{'='*60}\n")
    resultado = subprocess.run([sys.executable, script])
    if resultado.returncode != 0:
        print(f"\n{script} termino con error (codigo {resultado.returncode}). Abortando.")
        sys.exit(resultado.returncode)

print(
    "\nListo. Checkpoints en data/processed/*.pkl y graficas en eda/img/, "
    "feature_engineering/img/ y modeling/img_pronosticos/. Ahora puedes abrir modeling/modelado.ipynb."
)
