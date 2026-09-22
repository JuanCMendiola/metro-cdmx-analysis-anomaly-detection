# Orquestador: corre data/recoleccion_y_limpieza.py, eda/analisis_exploratorio.py
# y feature_engineering/feature_engineering.py en orden, cada uno como proceso
# independiente, para dejar listos los checkpoints (data/processed/*.pkl) y las
# graficas que necesita modeling/modelado.ipynb. Pensado para correr una sola
# vez despues de clonar el repo (o cuando quieras regenerar todo desde cero).
#
# Correr con la raiz del repo como working directory:
#   python setup_pipeline.py

import subprocess
import sys

PASOS = [
    ("1/3", "data/recoleccion_y_limpieza.py"),
    ("2/3", "eda/analisis_exploratorio.py"),
    ("3/3", "feature_engineering/feature_engineering.py"),
]

for numero, script in PASOS:
    print(f"\n{'='*60}\nPaso {numero}: {script}\n{'='*60}\n")
    resultado = subprocess.run([sys.executable, script])
    if resultado.returncode != 0:
        print(f"\n{script} termino con error (codigo {resultado.returncode}). Abortando.")
        sys.exit(resultado.returncode)

print(
    "\nListo. Checkpoints en data/processed/*.pkl y graficas en eda/img/ y "
    "feature_engineering/img/. Ahora puedes abrir modeling/modelado.ipynb."
)
