"""
API tests for Kanban boards and tasks.

Assumptions:
- Auth: POST /api/auth/login/ -> {"token", "user_id", "email", "fullname"}
- Boards: /api/kanban/boards/
- Tasks:  /api/kanban/tasks/
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


class KanbanApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            email="owner@example.com", fullname="Owner", password="pwOwner123"
        )
        self.member = user_model.objects.create_user(
            email="member@example.com", fullname="Member", password="pwMember123"
        )
        self.stranger = user_model.objects.create_user(
            email="stranger@example.com", fullname="Stranger", password="pwStrgr123"
        )
        self.board = Board.objects.create(title="B1", owner=self.owner)
        self.board.members.add(self.member)

    def test_unauthenticated_cannot_create_board(self):
        res = self.client.post(
            "/api/kanban/boards/", {"title": "Fail"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_create_and_list_own_board(self):
        auth(self.client, "owner@example.com", "pwOwner123")
        res = self.client.post(
            "/api/kanban/boards/", {"title": "New"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res2 = self.client.get("/api/kanban/boards/")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res2.data), 1)

    def test_member_sees_board_but_cannot_update(self):
        auth(self.client, "member@example.com", "pwMember123")
        r_get = self.client.get(f"/api/kanban/boards/{self.board.id}/")
        self.assertEqual(r_get.status_code, status.HTTP_200_OK)
        r_patch = self.client.patch(
            f"/api/kanban/boards/{self.board.id}/",
            {"title": "Nope"},
            format="json",
        )
        self.assertEqual(r_patch.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_cannot_see_foreign_board(self):
        auth(self.client, "stranger@example.com", "pwStrgr123")
        r = self.client.get(f"/api/kanban/boards/{self.board.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_create_task_on_own_board(self):
        auth(self.client, "owner@example.com", "pwOwner123")
        res = self.client.post(
            "/api/kanban/tasks/",
            {
                "title": "First task",
                "board": self.board.id,
                "priority": Task.Priority.MEDIUM,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_member_can_create_task_in_shared_board(self):
        auth(self.client, "member@example.com", "pwMember123")
        res = self.client.post(
            "/api/kanban/tasks/",
            {
                "title": "Task 1",
                "board": self.board.id,
                "priority": Task.Priority.LOW,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Task.objects.filter(title="Task 1", board=self.board).exists()
        )

    def test_move_task_changes_status(self):
        auth(self.client, "owner@example.com", "pwOwner123")
        t = Task.objects.create(
            title="X", board=self.board, priority=Task.Priority.MEDIUM
        )
        res = self.client.patch(
            f"/api/kanban/tasks/{t.id}/",
            {"status": Task.Status.DONE},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
