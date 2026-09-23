"""Búsqueda, filtros, orden y paginación — tanto la función pura
filter_user_library() como el comportamiento HTTP de la lista."""

import pytest
from django.http import QueryDict
from django.urls import reverse

from library.models import MediaItem, UserMedia
from library.queries import filter_user_library

pytestmark = pytest.mark.django_db


def _qd(**params):
    qd = QueryDict(mutable=True)
    for key, value in params.items():
        qd[key] = value
    return qd


class TestFilterUserLibraryFunction:
    def test_partial_title_search_is_case_insensitive(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Breaking Bad"))
        make_user_media(user, make_media(title="Dark"))
        base = UserMedia.objects.filter(user=user)

        result = filter_user_library(_qd(q="breaking"), base)
        assert result.count() == 1
        assert result.first().media.title == "Breaking Bad"

    def test_filter_by_status(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), status="completed")
        make_user_media(user, make_media(title="B"), status="planned")
        base = UserMedia.objects.filter(user=user)

        result = filter_user_library(_qd(status="completed"), base)
        assert result.count() == 1
        assert result.first().media.title == "A"

    def test_filter_by_media_type(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Peli", media_type="movie"))
        make_user_media(user, make_media(title="Serie", media_type="series"))
        base = UserMedia.objects.filter(user=user)

        result = filter_user_library(_qd(media_type="series"), base)
        assert result.count() == 1
        assert result.first().media.title == "Serie"

    def test_filter_by_favorite(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Fav"), favorite=True)
        make_user_media(user, make_media(title="NoFav"), favorite=False)
        base = UserMedia.objects.filter(user=user)

        result = filter_user_library(_qd(favorite="1"), base)
        assert result.count() == 1
        assert result.first().media.title == "Fav"

    def test_invalid_status_is_ignored_not_crashed(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"))
        base = UserMedia.objects.filter(user=user)
        result = filter_user_library(_qd(status="no_existe"), base)
        assert result.count() == 1  # se ignora el filtro inválido, no se rompe

    def test_invalid_sort_falls_back_to_default(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"))
        base = UserMedia.objects.filter(user=user)
        result = filter_user_library(_qd(sort="algo_raro"), base)
        assert list(result)  # no lanza excepción, usa el orden por defecto

    def test_combined_filters_do_not_erase_each_other(self, user, make_media, make_user_media):
        """Regresión del bug real de la Fase 8.5: combinar status + media_type
        no debía perder ninguno de los dos filtros."""
        make_user_media(user, make_media(title="Match", media_type="series"), status="completed")
        make_user_media(user, make_media(title="Solo tipo", media_type="series"), status="planned")
        make_user_media(user, make_media(title="Solo estado", media_type="movie"), status="completed")
        base = UserMedia.objects.filter(user=user)

        result = filter_user_library(_qd(status="completed", media_type="series"), base)
        assert result.count() == 1
        assert result.first().media.title == "Match"


class TestLibraryListHTTP:
    def test_pagination_limits_results_per_page(self, client, user, make_media, make_user_media):
        for i in range(15):
            make_user_media(user, make_media(title=f"Título {i}"))
        client.force_login(user)
        response = client.get(reverse("library:list"))
        assert len(response.context["page"].object_list) == 12  # LIBRARY_PAGE_SIZE

    def test_querystring_preserved_across_pages(self, client, user, make_media, make_user_media):
        for i in range(15):
            make_user_media(user, make_media(title=f"Serie {i}", media_type="series"))
        client.force_login(user)
        response = client.get(reverse("library:list"), {"media_type": "series", "page": 2})
        assert "media_type=series" in response.context["querystring"]

    def test_isolation_in_search_results(self, client, user, make_user, make_media, make_user_media):
        make_user_media(user, make_media(title="Mío"))
        other = make_user(username="otro")
        make_user_media(other, make_media(title="Ajeno"))

        client.force_login(user)
        response = client.get(reverse("library:list"))
        titles = [entry.media.title for entry in response.context["page"].object_list]
        assert titles == ["Mío"]
