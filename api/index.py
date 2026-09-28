"""Punto de entrada que espera Vercel para desplegar Django como función
serverless (@vercel/python). No es parte de Django en sí — es un adaptador
fino: expone la misma WSGI app de config/wsgi.py bajo el nombre `app`, que
es la convención que busca el builder de Vercel."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

print("[api/index] modulo importado", flush=True)

from django.core.wsgi import get_wsgi_application  # noqa: E402

_django_app = get_wsgi_application()

print("[api/index] django wsgi app creada", flush=True)


def app(environ, start_response):
    print(
        f"[api/index] request: PATH_INFO={environ.get('PATH_INFO')!r} "
        f"QUERY_STRING={environ.get('QUERY_STRING')!r} "
        f"SCRIPT_NAME={environ.get('SCRIPT_NAME')!r} "
        f"REQUEST_URI={environ.get('REQUEST_URI')!r} "
        f"RAW_URI={environ.get('RAW_URI')!r}",
        flush=True,
    )
    return _django_app(environ, start_response)
