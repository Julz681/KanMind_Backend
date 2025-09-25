"""
Django AppConfig for the authentication app.
Creates a reusable guest user after migrations are applied.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AuthAppConfig(AppConfig):
    """
    Configuration class for the auth_app.
    Uses post_migrate to avoid DB access during app initialization.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"

    def ready(self):
        from .guest import ensure_guest_user

        def _create_guest(**kwargs):
            try:
                ensure_guest_user()
            except Exception:
                # Ignore errors (e.g., database not migrated yet)
                pass  # pragma: no cover

        post_migrate.connect(_create_guest, sender=self)
