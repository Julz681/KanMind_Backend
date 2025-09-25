"""
Project URL configuration.

Provides both the new and legacy API paths so older frontends continue to work:
- /api/...                  (legacy)
- /api/kanban/...           (new)
- /api/auth/...             (auth endpoints)
- legacy auth aliases: /api/login/, /api/registration/, /api/email-check/
"""

from django.contrib import admin
from django.urls import include, path
from auth_app.api.views import EmailCheckView, LoginView, RegistrationView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (new)
    path("api/auth/", include("auth_app.api.urls")),

    # Kanban – new + legacy prefixes (both point to the same routes)
    path("api/kanban/", include("kanban_app.api.urls")),
    path("api/", include("kanban_app.api.urls")),

    # Legacy auth aliases for older frontends
    path("api/login/", LoginView.as_view(), name="login-compat"),
    path("api/registration/", RegistrationView.as_view(), name="registration-compat"),
    path("api/email-check/", EmailCheckView.as_view(), name="email-check-compat"),
]
