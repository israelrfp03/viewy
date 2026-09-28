#!/bin/bash
# Ejecutado por Vercel durante el build (ver "buildCommand" en vercel.json).
# Orden importante: primero npm (deja listo output.css y el vendor de
# Chart.js con su .map), luego collectstatic (que necesita esos ficheros
# ya generados para poder copiarlos y post-procesarlos con WhiteNoise).
set -o errexit

npm install
npm run build:css

python3.12 -m pip install -r requirements.txt
python3.12 manage.py collectstatic --noinput
