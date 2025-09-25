"""ASGI config (framework boilerplate)."""  # pragma: no cover
import os  # pragma: no cover
from django.core.asgi import get_asgi_application  # pragma: no cover

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # pragma: no cover
application = get_asgi_application()  # pragma: no cover
