"""
Integration tests for comments, task assignments, and dashboard stats.

Assumptions based on the current project:
- Auth endpoints:
    POST /api/auth/login/  -> returns {"token", "user_id", "email", "fullname"}
- Kanban endpoints:
    POST /api/kanban/comments/  (fields: task, content)
    GET  /api/kanban/comments/?task=<id>  -> list filtered by task
    GET  /api/kanban/tasks/<id>/          -> includes "comments_count"
    PATCH /api/kanban/tasks/<id>/         -> can set assignee/reviewer
    GET  /api/kanban/tasks/?assigned_to_me=true
    GET  /api/kanban/dashboard/           -> {"tickets_total","by_priority","by_status"}
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from kanban_app.models import Board, Task


def auth(client, email, password):
    """
    Authenticate test client using TokenAuthentication.
    Sets Authorization: Token <key> header on success.
    """
    res = client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    assert res.status_code == status.HTTP_200_OK, "Login failed in test setup"
    client.credentials(HTTP_AUTHORIZATION=f"Token {res.data['token']}")


class CommentAndDashboardTests(APITestCase):
    """
    End-to-end tests covering:
    - Creating and listing comments
    - Patching reviewer/assignee and filtering "assigned_to_me"
    - Reading dashboard summary stats
    """

    def setUp(self):
        user_model = get_user_model()

        self.owner = user_model.objects.create_user(
            email="owner@example.com", fullname="Owner", password="pwowner123"
        )
        self.member = user_model.objects.create_user(
            email="member@example.com", fullname="Member", password="pwmember123"
        )

        self.board = Board.objects.create(title="Board B", owner=self.owner)
        self.board.members.add(self.member)

        self.t1 = Task.objects.create(
            title="T1",
            board=self.board,
            priority=Task.Priority.LOW,
            status=Task.Status.TODO,
        )
        self.t2 = Task.objects.create(
            title="T2",
            board=self.board,
            priority=Task.Priority.HIGH,
            status=Task.Status.REVIEW,
        )

    def test_comment_create_and_filter(self):
        """Create a comment and verify filtering by task and count on detail."""
        auth(self.client, "member@example.com", "pwmember123")

        res = self.client.post(
            "/api/kanban/comments/",
            {"task": self.t1.id, "content": "looks good"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res2 = self.client.get(f"/api/kanban/comments/?task={self.t1.id}")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data), 1)

        res3 = self.client.get(f"/api/kanban/tasks/{self.t1.id}/")
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.data["comments_count"], 1)

    def test_reviewer_patch_and_assigned_filter(self):
        """Set reviewer/assignee then filter tasks assigned to the member."""
        auth(self.client, "owner@example.com", "pwowner123")

        res = self.client.patch(
            f"/api/kanban/tasks/{self.t2.id}/",
            {"reviewer": self.member.id, "assignee": self.member.id},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        auth(self.client, "member@example.com", "pwmember123")
        res2 = self.client.get("/api/kanban/tasks/?assigned_to_me=true")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertTrue(any(t["id"] == self.t2.id for t in res2.data))

    def test_dashboard_stats(self):
        """Dashboard endpoint returns expected aggregate keys."""
        auth(self.client, "owner@example.com", "pwowner123")

        res = self.client.get("/api/kanban/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tickets_total", res.data)
        self.assertIn("by_priority", res.data)
        self.assertIn("by_status", res.data)
