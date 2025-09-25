"""
Kanban domain models: Board, BoardMember, Task, and Comment.
Provides a minimal schema with clear relations and useful helpers.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Board(models.Model):
    """A board with a title and an owner. Members via through-model."""

    title = models.CharField(max_length=200)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )
    members = models.ManyToManyField(
        User, through="BoardMember", related_name="member_boards", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    def __str__(self) -> str:
        return f"{self.title} (#{self.id})"


class BoardMember(models.Model):
    """Through table for board memberships (owner is implicit member)."""

    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="board_memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_memberships"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("board", "user")
        ordering = ["board_id", "user_id"]
        verbose_name = "Board member"
        verbose_name_plural = "Board members"

    def __str__(self) -> str:
        return f"Board #{self.board_id} ↔ {self.user}"


class Task(models.Model):
    """A task on a board with assignees, priority, status, and due date."""

    class Status(models.TextChoices):
        TODO = "to-do", "To-do"
        IN_PROGRESS = "in-progress", "In progress"
        REVIEW = "review", "Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="review_tasks",
        null=True,
        blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["board", "status"]),
            models.Index(fields=["due_date"]),
        ]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self) -> str:
        return f"{self.title} (#{self.id})"

    @property
    def is_overdue(self) -> bool:
        """
        Return True if the task is overdue (due_date in the past).
        Tasks without a due_date are never considered overdue.
        """
        if not self.due_date:
            return False  # pragma: no cover (covered by tests focusing on dated tasks)
        return timezone.now().date() > self.due_date


class Comment(models.Model):
    """A user comment attached to a task."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self) -> str:
        return f"Comment #{self.id} on Task #{self.task_id}"
