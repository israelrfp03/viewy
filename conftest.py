"""Fixtures compartidas por toda la suite. pytest descubre este archivo
automáticamente sin necesidad de importarlo — disponible en cualquier test
de cualquier app.
"""

import pytest
from django.contrib.auth import get_user_model

from library.models import MediaItem, UserMedia

User = get_user_model()

DEFAULT_PASSWORD = "ContrasenaSegura123"


@pytest.fixture
def make_user(db):
    """Fábrica de usuarios. make_user() crea uno con datos por defecto;
    make_user(username="otro") permite variarlo."""

    def _make(username="ana", **kwargs):
        return User.objects.create_user(username=username, password=DEFAULT_PASSWORD, **kwargs)

    return _make


@pytest.fixture
def user(make_user):
    """Un usuario por defecto, listo para la mayoría de los tests."""
    return make_user()


@pytest.fixture
def make_media(db):
    def _make(title="Título de prueba", media_type=MediaItem.MediaType.MOVIE, **kwargs):
        return MediaItem.objects.create(title=title, media_type=media_type, **kwargs)

    return _make


@pytest.fixture
def make_user_media(db):
    def _make(user, media, **kwargs):
        return UserMedia.objects.create(user=user, media=media, **kwargs)

    return _make
