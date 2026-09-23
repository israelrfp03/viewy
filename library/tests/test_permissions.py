"""Aislamiento entre usuarios — la categoría de tests más importante del
proyecto. Cada vista que opera sobre un UserMedia debe devolver 404 (nunca
los datos, nunca un 403 que confirme que el registro existe) cuando el
usuario autenticado no es el dueño, tanto por GET como por POST."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def other_users_entry(make_user, make_media, make_user_media):
    """Un UserMedia que pertenece a otro usuario ("victima"), no al que
    hace la petición en el test."""
    owner = make_user(username="victima")
    media = make_media(title="Contenido de la víctima")
    return make_user_media(owner, media, rating=8)


class TestDetailPermissions:
    def test_owner_can_view_detail(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        response = client.get(reverse("library:detail", args=[entry.pk]))
        assert response.status_code == 200

    def test_other_user_cannot_view_detail(self, client, user, other_users_entry):
        client.force_login(user)
        response = client.get(reverse("library:detail", args=[other_users_entry.pk]))
        assert response.status_code == 404

    def test_anonymous_user_redirected_to_login(self, client, other_users_entry):
        response = client.get(reverse("library:detail", args=[other_users_entry.pk]))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


class TestUpdatePermissions:
    def test_owner_can_edit(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        response = client.post(
            reverse("library:update", args=[entry.pk]),
            {"status": "completed", "rating": 9, "review": "", "current_episode": 0},
        )
        assert response.status_code == 302
        entry.refresh_from_db()
        assert entry.status == "completed"
        assert entry.rating == 9

    def test_other_user_cannot_view_edit_form(self, client, user, other_users_entry):
        client.force_login(user)
        response = client.get(reverse("library:update", args=[other_users_entry.pk]))
        assert response.status_code == 404

    def test_other_user_cannot_edit_via_manipulated_post(self, client, user, other_users_entry):
        """El caso crítico: un POST bien formado a un pk ajeno no debe
        modificar nada, aunque el usuario conozca el pk."""
        client.force_login(user)
        original_rating = other_users_entry.rating
        response = client.post(
            reverse("library:update", args=[other_users_entry.pk]),
            {"status": "completed", "rating": 1, "review": "hackeado", "current_episode": 999},
        )
        assert response.status_code == 404
        other_users_entry.refresh_from_db()
        assert other_users_entry.rating == original_rating
        assert other_users_entry.review == ""


class TestDeletePermissions:
    def test_owner_can_delete(self, client, user, make_media, make_user_media):
        entry = make_user_media(user, make_media())
        client.force_login(user)
        response = client.post(reverse("library:delete", args=[entry.pk]))
        assert response.status_code == 302
        assert not entry.__class__.objects.filter(pk=entry.pk).exists()

    def test_other_user_cannot_delete(self, client, user, other_users_entry):
        client.force_login(user)
        response = client.post(reverse("library:delete", args=[other_users_entry.pk]))
        assert response.status_code == 404
        assert other_users_entry.__class__.objects.filter(pk=other_users_entry.pk).exists()


class TestLibraryListIsolation:
    def test_user_only_sees_own_entries(self, client, user, make_user, make_media, make_user_media):
        media_mine = make_media(title="Mi contenido")
        make_user_media(user, media_mine)

        other = make_user(username="otro")
        media_other = make_media(title="Contenido ajeno")
        make_user_media(other, media_other)

        client.force_login(user)
        response = client.get(reverse("library:list"))
        content = response.content.decode()
        assert "Mi contenido" in content
        assert "Contenido ajeno" not in content


class TestProtectedViewsRequireLogin:
    @pytest.mark.parametrize(
        "url_name",
        ["list", "create", "search"],
    )
    def test_view_redirects_to_login(self, client, url_name):
        response = client.get(reverse(f"library:{url_name}"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
