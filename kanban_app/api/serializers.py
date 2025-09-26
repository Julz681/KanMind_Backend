"""
Serializer-Schicht für Kanban-API gemäß Dokumentation.
Gibt exakt die in der Doku geforderten Felder zurück.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from kanban_app.models import Task, Comment

User = get_user_model()

# ---------- Gemeinsame, kleine Serializers ----------

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "fullname")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.fullname")

    class Meta:
        model = Comment
        fields = ("id", "created_at", "author", "content")


# ---------- Boards ----------

class BoardListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()
    owner_id = serializers.IntegerField()


class BoardCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    members = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

    def validate_members(self, ids):
        valid_ids = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = sorted(set(ids) - valid_ids)
        if missing:
            raise serializers.ValidationError(f"Unbekannte User-IDs: {', '.join(map(str, missing))}")
        return list(valid_ids)


class BoardCreateResponseSerializer(BoardListItemSerializer):
    pass


class BoardMemberSerializer(UserMiniSerializer):
    pass


class TaskOnBoardSerializer(serializers.ModelSerializer):
    assignee = UserMiniSerializer(allow_null=True)
    reviewer = UserMiniSerializer(allow_null=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        )


class BoardDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    owner_id = serializers.IntegerField()
    members = BoardMemberSerializer(many=True)
    tasks = TaskOnBoardSerializer(many=True)


class BoardUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    members = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate_members(self, ids):
        valid_ids = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = sorted(set(ids) - valid_ids)
        if missing:
            raise serializers.ValidationError(f"Unbekannte User-IDs: {', '.join(map(str, missing))}")
        return list(valid_ids)


class BoardUpdateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    owner_data = UserMiniSerializer()
    members_data = UserMiniSerializer(many=True)


# ---------- Tasks ----------

class TaskCreateSerializer(serializers.Serializer):
    board = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=["to-do", "in-progress", "review", "done"])
    priority = serializers.ChoiceField(choices=["low", "medium", "high"])
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class TaskDetailSerializer(serializers.ModelSerializer):
    board = serializers.IntegerField(source="board_id", read_only=True)
    assignee = UserMiniSerializer(allow_null=True)
    reviewer = UserMiniSerializer(allow_null=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = (
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
        )


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["to-do", "in-progress", "review", "done"], required=False)
    priority = serializers.ChoiceField(choices=["low", "medium", "high"], required=False)
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


# ---------- Comments ----------

class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
