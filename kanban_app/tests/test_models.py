"""
Model __str__ method tests for Kanban models.
Verifies human-readable string representations.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from kanban_app.models import Board, Task


class ModelStrTests(TestCase):
    """Ensure __str__ returns clear, expected values."""

    def test_str_methods(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="user@example.com", fullname="User", password="pwTest123"
        )

        board = Board.objects.create(title="Board A", owner=user)
        task = Task.objects.create(
            board=board,
            title="Task X",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.TODO,
        )

        self.assertIn("Board A", str(board))
        self.assertIn("Task X", str(task))
