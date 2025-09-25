"""
Serializers for Kanban API: users, tasks, comments, and boards.
Back-compat: BoardDetail also returns 'columns' and 'tickets' for old UIs.
"""

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers

from kanban_app.models import Board, BoardMember, Comment, Task

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Lightweight view of a user."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Write serializer used by the frontend to create/update tasks.
    Accepts: board (id), assignee_id, reviewer_id.
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
    """Read-only task details with nested users and comment count."""

    assignee = UserMiniSerializer(allow_null=True)
    reviewer = UserMiniSerializer(allow_null=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Comment with author full name for display."""

    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]


class BoardListSerializer(serializers.ModelSerializer):
    """
    Board list item with several aggregate counters and aliases
    (kept for compatibility with older frontends).
    """

    members_count = serializers.SerializerMethodField()
    tickets_count = serializers.SerializerMethodField()
    todo_count = serializers.SerializerMethodField()
    high_prio_count = serializers.SerializerMethodField()

    members = serializers.SerializerMethodField()
    tickets = serializers.SerializerMethodField()
    todos = serializers.SerializerMethodField()
    high_prio = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members_count",
            "tickets_count",
            "todo_count",
            "high_prio_count",
            "members",
            "tickets",
            "todos",
            "high_prio",
        ]

    def _members_count(self, obj):
        ids = set(
            BoardMember.objects.filter(board=obj).values_list("user_id", flat=True)
        )
        ids.add(obj.owner_id)
        return len(ids)

    def _tickets_count(self, obj):
        return Task.objects.filter(board=obj).count()

    def _todo_count(self, obj):
        return Task.objects.filter(board=obj, status=Task.Status.TODO).count()

    def _hp_count(self, obj):
        return Task.objects.filter(board=obj, priority=Task.Priority.HIGH).count()

    def get_members_count(self, obj):
        return self._members_count(obj)

    def get_tickets_count(self, obj):
        return self._tickets_count(obj)

    def get_todo_count(self, obj):
        return self._todo_count(obj)

    def get_high_prio_count(self, obj):
        return self._hp_count(obj)

    def get_members(self, obj):
        return self._members_count(obj)

    def get_tickets(self, obj):
        return self._tickets_count(obj)

    def get_todos(self, obj):
        return self._todo_count(obj)

    def get_high_prio(self, obj):
        return self._hp_count(obj)


class BoardMemberSerializer(serializers.ModelSerializer):
    """Expose user fields when listing board members."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed board view with members and tasks.
    Back-compat: also returns 'columns' and 'tickets' as older UIs expect.
    """

    owner_id = serializers.IntegerField()
    members = BoardMemberSerializer(many=True)
    tasks = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    tickets = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks", "columns", "tickets"]

    def get_tasks(self, obj):
        qs = (
            obj.tasks.select_related("assignee", "reviewer")
            .annotate(comments_count=models.Count("comments"))
        )
        return TaskDetailSerializer(qs, many=True).data

    def get_columns(self, obj):
        return [
            {"id": 0, "title": "To-do"},
            {"id": 1, "title": "In progress"},
            {"id": 2, "title": "Review"},
            {"id": 3, "title": "Done"},
        ]

    def get_tickets(self, obj):
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
