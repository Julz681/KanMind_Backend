"""
Additional API tests for Kanban listings.
Covers listing boards and tasks for a member of a shared board.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from kanban_app.models import Board, Task


def auth(client, email, password):
    """Login helper that sets Token auth header on the test client."""
    res = client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    assert res.status_code == status.HTTP_200_OK, "Login failed"
    client.credentials(HTTP_AUTHORIZATION=f"Token {res.data['token']}")


class KanbanMoreTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="own@example.com", fullname="Owner", password="pwOwner123"
        )
        self.member = user_model.objects.create_user(
            email="mem@example.com", fullname="Member", password="pwMember123"
        )
        self.board = Board.objects.create(title="B", owner=self.owner)
        self.board.members.add(self.member)
        Task.objects.create(
            title="T1", board=self.board, priority=Task.Priority.LOW
        )
        Task.objects.create(
            title="T2", board=self.board, priority=Task.Priority.MEDIUM
        )

    def test_member_can_list_boards(self):
        """Member should see the shared board in the list."""
        auth(self.client, "mem@example.com", "pwMember123")
        res = self.client.get("/api/kanban/boards/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(any(b["id"] == self.board.id for b in res.data))

    def test_member_can_list_tasks(self):
        """Member should list tasks from the shared board."""
        auth(self.client, "mem@example.com", "pwMember123")
        res = self.client.get("/api/kanban/tasks/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)
