"""Punto de entrada que espera Vercel para desplegar Django como función
serverless (@vercel/python). No es parte de Django en sí — es un adaptador
fino: expone la misma WSGI app de config/wsgi.py bajo el nombre `app`, que
es la convención que busca el builder de Vercel."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
