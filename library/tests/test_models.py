"""MediaItem y UserMedia: constraints y validaciones que protegen datos
incorrectos a nivel de base de datos. No se prueba comportamiento interno
de Django (ForeignKey, auto_now_add...) que ya garantiza el framework."""

import pytest
from django.db import IntegrityError, transaction

from library.models import MediaItem, UserMedia

pytestmark = pytest.mark.django_db


class TestMediaItem:
    def test_valid_creation(self, make_media):
        media = make_media(title="Breaking Bad", media_type="series", release_year=2008)
        assert media.pk is not None
        assert media.external_source == MediaItem.ExternalSource.MANUAL

    def test_release_year_before_1888_is_rejected(self, make_media):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_media(release_year=1800)

    def test_release_year_null_is_allowed(self, make_media):
        media = make_media(release_year=None)
        assert media.release_year is None

    def test_duplicate_external_id_for_same_source_is_rejected(self, make_media):
        make_media(external_source="tmdb", external_id="123")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_media(title="Otro título", external_source="tmdb", external_id="123")

    def test_empty_external_id_does_not_trigger_uniqueness(self, make_media):
        """Varias entradas manuales (external_id="") deben poder coexistir —
        la constraint solo aplica cuando external_id no está vacío."""
        make_media(title="Manual A", external_id="")
        media_b = make_media(title="Manual B", external_id="")
        assert media_b.pk is not None


class TestUserMedia:
    def test_valid_creation_defaults(self, user, make_media, make_user_media):
        media = make_media()
        entry = make_user_media(user, media)
        assert entry.status == UserMedia.Status.PLANNED
        assert entry.favorite is False
        assert entry.current_episode == 0
        assert entry.rating is None

    def test_rating_within_range_is_valid(self, user, make_media, make_user_media):
        entry = make_user_media(user, make_media(), rating=7)
        assert entry.rating == 7

    @pytest.mark.parametrize("invalid_rating", [0, -1, 11, 100])
    def test_rating_out_of_range_is_rejected(self, invalid_rating, user, make_media, make_user_media):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_user_media(user, make_media(), rating=invalid_rating)

    def test_same_user_cannot_add_same_media_twice(self, user, make_media, make_user_media):
        media = make_media()
        make_user_media(user, media)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_user_media(user, media)

    def test_two_different_users_can_add_same_media(self, make_user, make_media, make_user_media):
        media = make_media()
        user_a = make_user(username="a")
        user_b = make_user(username="b")
        make_user_media(user_a, media)
        entry_b = make_user_media(user_b, media)
        assert entry_b.pk is not None
