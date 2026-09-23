"""Cliente genérico de Gemini — mecánica HTTP pura, sin saber nada del
dominio de quien lo llama (eso lo valida cada app por su cuenta)."""

import requests

from integrations import gemini

SCHEMA = {"type": "OBJECT", "properties": {"x": {"type": "STRING"}}}


def test_successful_call_returns_parsed_dict(monkeypatch, settings):
    settings.GEMINI_API_KEY = "clave-de-prueba"

    def fake_post(*args, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {"candidates": [{"content": {"parts": [{"text": '{"x": "ok"}'}]}}]}
        return response

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    result = gemini.call_gemini("sistema", "usuario", SCHEMA)
    assert result == {"x": "ok"}


def test_missing_api_key_raises_config_error(settings):
    settings.GEMINI_API_KEY = ""
    try:
        gemini.call_gemini("sistema", "usuario", SCHEMA)
        assert False
    except gemini.GeminiConfigError:
        pass


def test_timeout_raises_gemini_timeout_error(monkeypatch, settings):
    settings.GEMINI_API_KEY = "clave"

    def fake_post(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    try:
        gemini.call_gemini("sistema", "usuario", SCHEMA)
        assert False
    except gemini.GeminiTimeoutError:
        pass


def test_rate_limit_raises_generic_error(monkeypatch, settings):
    settings.GEMINI_API_KEY = "clave"

    def fake_post(*args, **kwargs):
        response = requests.Response()
        response.status_code = 429
        response.json = lambda: {}
        return response

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    try:
        gemini.call_gemini("sistema", "usuario", SCHEMA)
        assert False
    except gemini.GeminiError:
        pass


def test_malformed_json_text_raises_response_error(monkeypatch, settings):
    settings.GEMINI_API_KEY = "clave"

    def fake_post(*args, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {"candidates": [{"content": {"parts": [{"text": "esto no es json"}]}}]}
        return response

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    try:
        gemini.call_gemini("sistema", "usuario", SCHEMA)
        assert False
    except gemini.GeminiResponseError:
        pass


def test_unexpected_response_shape_raises_response_error(monkeypatch, settings):
    settings.GEMINI_API_KEY = "clave"

    def fake_post(*args, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {"unexpected": "shape"}
        return response

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    try:
        gemini.call_gemini("sistema", "usuario", SCHEMA)
        assert False
    except gemini.GeminiResponseError:
        pass
