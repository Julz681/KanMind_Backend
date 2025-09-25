"""
Admin configuration for Kanban app models.
Provides management interfaces for boards, tasks, members, and comments.
"""

from django.contrib import admin
from .models import Board, BoardMember, Task, Comment


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """
    Admin interface for Board model.
    Allows searching by title and owner and provides autocomplete for owner.
    """

    list_display = ("id", "title", "owner", "created_at")
    search_fields = ("title", "owner__email", "owner__fullname")
    list_filter = ("created_at",)
    autocomplete_fields = ("owner",)  # keep for quick owner selection


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for BoardMember model.
    Enables quick lookup of boards and users.
    """

    list_display = ("board", "user", "added_at")
    search_fields = ("board__title", "user__email", "user__fullname")
    autocomplete_fields = ("board", "user")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    Includes filters, search, and autocompletion for related fields.
    """

    list_display = (
        "id",
        "title",
        "board",
        "status",
        "priority",
        "assignee",
        "reviewer",
        "due_date",
    )
    list_filter = ("status", "priority", "board")
    search_fields = (
        "title",
        "description",
        "assignee__email",
        "reviewer__email",
    )
    autocomplete_fields = ("board", "assignee", "reviewer")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin interface for Comment model.
    Supports search and autocomplete for task and author.
    """

    list_display = ("id", "task", "author", "created_at")
    search_fields = ("task__title", "author__email", "content")
    autocomplete_fields = ("task", "author")
