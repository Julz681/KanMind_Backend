"""
Utility to ensure a reusable guest account exists for demos/dev.
"""

import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError


def ensure_guest_user():
    """Create a guest account if missing (idempotent)."""
    try:
        User = get_user_model()
        email = os.environ.get("GUEST_EMAIL", "gast@test.de")
        pwd = os.environ.get("GUEST_PASSWORD", "guest123")
        if not User.objects.filter(email=email).exists():
            User.objects.create_user(email=email, password=pwd, fullname="Guest")
    except (OperationalError, ProgrammingError):
        # Happens before migrations; safe to ignore in tests
        pass  # pragma: no cover
