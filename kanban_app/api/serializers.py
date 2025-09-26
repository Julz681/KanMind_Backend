"""
Serializer layer for the Kanban API as defined in the documentation.
Returns exactly the fields required by the specification.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from kanban_app.models import Task, Comment

User = get_user_model()

# ---------- Shared, small serializers ----------


class UserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer exposing only basic identity information.
    Provides id, email, and full name for lightweight embedding.
    """
    class Meta:
        model = User
        fields = ("id", "email", "fullname")


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    Includes author full name, creation timestamp and comment content.
    """
    author = serializers.CharField(source="author.fullname")

    class Meta:
        model = Comment
        fields = ("id", "created_at", "author", "content")


# ---------- Boards ----------


class BoardListItemSerializer(serializers.Serializer):
    """
    Lightweight serializer representing a board in list views.
    Includes counts for members, tickets, tasks to do, and high priority tasks.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()
    owner_id = serializers.IntegerField()


class BoardCreateSerializer(serializers.Serializer):
    """
    Serializer used to create a new board.
    Accepts a title and an optional list of member user IDs.
    """
    title = serializers.CharField()
    members = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

    def validate_members(self, ids):
        """
        Validate that all provided member IDs exist in the database.
        Raises ValidationError if any unknown user IDs are found.
        """
        valid_ids = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = sorted(set(ids) - valid_ids)
        if missing:
            raise serializers.ValidationError(
                f"Unknown user IDs: {', '.join(map(str, missing))}"
            )
        return list(valid_ids)


class BoardCreateResponseSerializer(BoardListItemSerializer):
    """
    Response serializer for board creation.
    Reuses the list item representation for convenience.
    """
    pass


class BoardMemberSerializer(UserMiniSerializer):
    """
    Serializer for board members using the minimal user representation.
    """
    pass


class TaskOnBoardSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks when they are included inside a board representation.
    Includes assignee, reviewer, and comment count.
    """
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
    """
    Detailed board serializer.
    Contains board information, members, and all related tasks.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    owner_id = serializers.IntegerField()
    members = BoardMemberSerializer(many=True)
    tasks = TaskOnBoardSerializer(many=True)


class BoardUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a board.
    Allows partial updates of title and member list.
    """
    title = serializers.CharField(required=False)
    members = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate_members(self, ids):
        """
        Validate that updated member IDs exist in the database.
        Raises ValidationError if any unknown user IDs are found.
        """
        valid_ids = set(User.objects.filter(id__in=ids).values_list("id", flat=True))
        missing = sorted(set(ids) - valid_ids)
        if missing:
            raise serializers.ValidationError(
                f"Unknown user IDs: {', '.join(map(str, missing))}"
            )
        return list(valid_ids)


class BoardUpdateResponseSerializer(serializers.Serializer):
    """
    Response serializer after a board update.
    Returns updated title, owner data and full member list.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    owner_data = UserMiniSerializer()
    members_data = UserMiniSerializer(many=True)


# ---------- Tasks ----------


class TaskCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new task.
    Accepts board ID, title, optional description, status, priority,
    optional assignee/reviewer IDs, and an optional due date.
    """
    board = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    status = serializers.ChoiceField(
        choices=["to-do", "in-progress", "review", "done"]
    )
    priority = serializers.ChoiceField(choices=["low", "medium", "high"])
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed task serializer for retrieving a single task.
    Includes related board ID, assignee/reviewer details, and comment count.
    """
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
    """
    Serializer for updating an existing task.
    All fields are optional to allow partial updates.
    """
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=["to-do", "in-progress", "review", "done"], required=False
    )
    priority = serializers.ChoiceField(
        choices=["low", "medium", "high"], required=False
    )
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


# ---------- Comments ----------


class CommentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new comment on a task.
    Requires only the comment content.
    """
    content = serializers.CharField()
