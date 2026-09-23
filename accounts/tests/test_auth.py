"""Autenticación: registro, login, logout, acceso a vistas protegidas."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_register_with_valid_data_creates_user(client, django_user_model):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "nuevo",
            "email": "nuevo@example.com",
            "password1": "ContrasenaSegura123",
            "password2": "ContrasenaSegura123",
        },
    )
    assert response.status_code == 302
    assert django_user_model.objects.filter(username="nuevo").exists()


def test_register_with_mismatched_passwords_does_not_create_user(client, django_user_model):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "nuevo",
            "email": "nuevo@example.com",
            "password1": "ContrasenaSegura123",
            "password2": "OtraDistinta456",
        },
    )
    assert response.status_code == 200  # se queda en el formulario, no redirige
    assert not django_user_model.objects.filter(username="nuevo").exists()


def test_register_with_common_password_is_rejected(client, django_user_model):
    response = client.post(
        reverse("accounts:register"),
        {"username": "nuevo", "email": "", "password1": "password123", "password2": "password123"},
    )
    assert response.status_code == 200
    assert not django_user_model.objects.filter(username="nuevo").exists()


def test_register_redirects_authenticated_user_to_profile(client, user):
    client.force_login(user)
    response = client.get(reverse("accounts:register"))
    assert response.status_code == 302
    assert response.url == reverse("accounts:profile")


def test_login_with_correct_credentials_succeeds(client, make_user):
    make_user(username="ana")
    response = client.post(
        reverse("accounts:login"), {"username": "ana", "password": "ContrasenaSegura123"}
    )
    assert response.status_code == 302


def test_login_with_wrong_password_fails(client, make_user):
    make_user(username="ana")
    response = client.post(reverse("accounts:login"), {"username": "ana", "password": "incorrecta"})
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_logout_ends_session(client, user):
    client.force_login(user)
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


def test_profile_requires_login(client):
    response = client.get(reverse("accounts:profile"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_profile_accessible_when_logged_in(client, user):
    client.force_login(user)
    response = client.get(reverse("accounts:profile"))
    assert response.status_code == 200


def test_user_bio_defaults_to_blank(user):
    assert user.bio == ""
