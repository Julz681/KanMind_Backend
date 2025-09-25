"""
Django AppConfig for the Kanban application.
Defines default settings for model primary keys.
"""

from django.apps import AppConfig


class KanbanAppConfig(AppConfig):
    """
    Configuration class for the kanban_app.
    Sets the default auto field for database models.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "kanban_app"
