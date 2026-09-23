"""CRUD de biblioteca: crear, editar cada campo relevante, borrar. Se prueba
comportamiento (qué queda guardado), no HTML."""

import pytest
from django.urls import reverse

from library.models import MediaItem, UserMedia

pytestmark = pytest.mark.django_db


class TestCreate:
    def test_manual_creation_creates_media_and_entry(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse("library:create"),
            {
                "title": "Mi película",
                "media_type": "movie",
                "release_year": 2020,
                "description": "",
                "duration_minutes": "",
                "episodes": "",
                "status": "planned",
                "rating": "",
                "review": "",
                "current_episode": 0,
            },
        )
        assert response.status_code == 302
        assert MediaItem.objects.filter(title="Mi película").exists()
        assert UserMedia.objects.filter(user=user, media__title="Mi película").exists()

    def test_creating_same_title_twice_reuses_media_item(self, client, user, make_user, make_media):
        """Dos usuarios añadiendo el mismo título manual no deben duplicar
        el MediaItem — solo el UserMedia es por usuario."""
        media = make_media(title="Compartida", media_type="movie")
        other = make_user(username="otro")
        UserMedia.objects.create(user=other, media=media)

        client.force_login(user)
        client.post(
            reverse("library:create"),
            {
                "title": "Compartida", "media_type": "movie", "release_year": "",
                "description": "", "duration_minutes": "", "episodes": "",
                "status": "planned", "rating": "", "review": "", "current_episode": 0,
            },
        )
        assert MediaItem.objects.filter(title="Compartida").count() == 1

    def test_cannot_add_same_media_twice_for_same_user(self, client, user, make_media):
        media = make_media(title="Duplicada", media_type="movie")
        UserMedia.objects.create(user=user, media=media)

        client.force_login(user)
        response = client.post(
            reverse("library:create"),
            {
                "title": "Duplicada", "media_type": "movie", "release_year": "",
                "description": "", "duration_minutes": "", "episodes": "",
                "status": "planned", "rating": "", "review": "", "current_episode": 0,
            },
        )
        assert response.status_code == 200  # se queda en el formulario con el error
        assert UserMedia.objects.filter(user=user, media=media).count() == 1


class TestUpdate:
    def _post_update(self, client, entry, **overrides):
        data = {
            "status": "watching", "rating": "", "review": "",
            "started_at": "", "finished_at": "", "current_episode": 0,
        }
        data.update(overrides)
        return client.post(reverse("library:update", args=[entry.pk]), data)

    def test_update_status(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        self._post_update(client, entry, status="completed")
        entry.refresh_from_db()
        assert entry.status == "completed"

    def test_update_rating(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        self._post_update(client, entry, rating=8)
        entry.refresh_from_db()
        assert entry.rating == 8

    def test_update_review(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        self._post_update(client, entry, review="Muy buena")
        entry.refresh_from_db()
        assert entry.review == "Muy buena"

    def test_update_favorite(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        self._post_update(client, entry, favorite="on")
        entry.refresh_from_db()
        assert entry.favorite is True

    def test_update_dates(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        self._post_update(client, entry, started_at="2026-01-01", finished_at="2026-01-15")
        entry.refresh_from_db()
        assert str(entry.started_at) == "2026-01-01"
        assert str(entry.finished_at) == "2026-01-15"

    def test_update_current_episode(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media(media_type="series"))
        client.force_login(user)
        self._post_update(client, entry, current_episode=5)
        entry.refresh_from_db()
        assert entry.current_episode == 5

    def test_invalid_rating_does_not_save(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media(), rating=5)
        client.force_login(user)
        self._post_update(client, entry, rating=99)
        entry.refresh_from_db()
        assert entry.rating == 5  # sin cambios, el formulario rechaza el valor


class TestDelete:
    def test_delete_removes_user_media_but_keeps_media_item(self, client, user, make_media, make_user_media):
        media = make_media()
        entry = make_user_media(user, media)
        client.force_login(user)
        client.post(reverse("library:delete", args=[entry.pk]))
        assert not UserMedia.objects.filter(pk=entry.pk).exists()
        assert MediaItem.objects.filter(pk=media.pk).exists()
