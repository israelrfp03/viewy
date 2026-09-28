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
    raw_path_info = environ.get("PATH_INFO", "")

    # TEMPORAL: bypass incondicional para todas las peticiones, para ver el
    # environ real que construye Vercel sin depender de ninguna condición
    # sobre PATH_INFO/QUERY_STRING (las dos veces que probamos a activarlo
    # solo para ciertas rutas/queries, nunca se disparó, así que dejamos de
    # adivinar y volcamos el environ siempre). Quitar en cuanto el routing
    # quede confirmado.
    body = "\n".join(
        f"{key}={value!r}"
        for key, value in sorted(environ.items())
        if isinstance(value, (str, int, float, bool))
    ).encode("utf-8")
    start_response(
        "200 OK",
        [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body)))],
    )
    return [body]

    path_info = raw_path_info
    if path_info.startswith(_REWRITE_PREFIX):
        path_info = path_info[len(_REWRITE_PREFIX):]
    environ["PATH_INFO"] = path_info or "/"

    # TEMPORAL: cabecera de depuración para ver en producción qué PATH_INFO
    # llega realmente desde Vercel, sin adivinar a ciegas. Quitar en cuanto
    # el routing quede confirmado.
    def debug_start_response(status, headers, exc_info=None):
        headers = list(headers) + [
            ("X-Debug-Raw-Path-Info", raw_path_info or "(empty)"),
            ("X-Debug-Script-Name", environ.get("SCRIPT_NAME", "") or "(empty)"),
        ]
        return start_response(status, headers, exc_info)

    return _django_app(environ, debug_start_response)
