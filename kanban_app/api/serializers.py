"""
Serializers for Kanban API: users, tasks, comments, and boards.
Back-compat: BoardDetail returns 'columns' and (optional) 'tickets'
and verwendet exakt die Keys, die die Tests erwarten.
"""

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers

from kanban_app.models import Board, BoardMember, Comment, Task

User = get_user_model()


# --------- User ---------
class UserMiniSerializer(serializers.ModelSerializer):
    """Leichte Darstellung eines Users (id, email, fullname)."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


# --------- Tasks ---------
class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Write-Serializer zum Erstellen/Ändern von Tasks.
    Erwartet: board (id), assignee_id, reviewer_id.
    """

    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all())
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="assignee", required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="reviewer", required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Read-Serializer für Tasks (kompletter Task im Response).
    Wichtig: 'board_id' statt 'board' und verschachtelte User-Objekte.
    """

    board_id = serializers.IntegerField(read_only=True)
    assignee = UserMiniSerializer(allow_null=True)
    reviewer = UserMiniSerializer(allow_null=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board_id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]


# --------- Comments ---------
class CommentSerializer(serializers.ModelSerializer):
    """Kommentar mit Autor-Vollname für die Anzeige."""

    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]


# --------- Boards (Liste) ---------
class BoardListSerializer(serializers.ModelSerializer):
    """
    Exaktes List-Item für Boards – die Tests erwarten:
    { id, title, member_count }
    """

    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "member_count"]

    def get_member_count(self, obj):
        # Owner zählt immer als Mitglied
        ids = set(BoardMember.objects.filter(board=obj).values_list("user_id", flat=True))
        ids.add(obj.owner_id)
        return len(ids)


# --------- Boards (Detail) ---------
class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailansicht eines Boards.
    Erwartet: owner_data (Objekt) + members (Liste von Objekten).
    'columns' bleibt für Legacy-UIs.
    'tickets' nur beibehalten, falls deine Tests es erwarten.
    """

    owner_data = UserMiniSerializer(source="owner", read_only=True)
    members = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    tickets = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members", "columns", "tickets"]

    def get_members(self, obj):
        # Owner + alle BoardMember als eindeutige Users
        user_ids = set(BoardMember.objects.filter(board=obj).values_list("user_id", flat=True))
        user_ids.add(obj.owner_id)
        qs = User.objects.filter(id__in=list(user_ids)).order_by("id")
        return UserMiniSerializer(qs, many=True).data

    def get_columns(self, obj):
        return [
            {"id": 0, "title": "To-do"},
            {"id": 1, "title": "In progress"},
            {"id": 2, "title": "Review"},
            {"id": 3, "title": "Done"},
        ]

    def get_tickets(self, obj):
        # Falls die Tests 'tickets' nicht brauchen: Feld aus Meta.fields entfernen.
        status_to_col = {"to-do": 0, "in-progress": 1, "review": 2, "done": 3}
        qs = obj.tasks.all().select_related("assignee", "reviewer")
        items = []
        for t in qs:
            items.append(
                {
                    "id": t.id,
                    "title": t.title,
                    "column": status_to_col.get(t.status, 0),
                    "priority": t.priority,
                    "assignee": t.assignee_id,
                    "reviewer": t.reviewer_id,
                    "description": t.description,
                    "due_date": t.due_date,
                }
            )
        return items
