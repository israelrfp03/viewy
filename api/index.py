"""Punto de entrada que espera Vercel para desplegar Django como función
serverless (@vercel/python). No es parte de Django en sí — es un adaptador
fino: expone la misma WSGI app de config/wsgi.py bajo el nombre `app`, que
es la convención que busca el builder de Vercel.

El rewrite de vercel.json manda toda petición a "/api/index/<ruta original>"
(con la ruta capturada vía $1), así que aquí quitamos ese prefijo del
PATH_INFO antes de pasarle la petición a Django: si no lo hiciéramos,
Django vería PATH_INFO="/api/index/admin/" en vez de "/admin/" y ningún
patrón de urls.py encajaría nunca (todo devolvería 404)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

_django_app = get_wsgi_application()

_REWRITE_PREFIX = "/api/index"


def app(environ, start_response):
    path_info = environ.get("PATH_INFO", "")
    if path_info.startswith(_REWRITE_PREFIX):
        path_info = path_info[len(_REWRITE_PREFIX):]
    environ["PATH_INFO"] = path_info or "/"
    return _django_app(environ, start_response)
