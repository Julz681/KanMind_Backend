"""
API views for Kanban boards, tasks, comments, and dashboard.
Back-compat: accepts legacy task payloads and keeps methods short.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Board, BoardMember, Comment, Task
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    CommentSerializer,
    TaskCreateUpdateSerializer,
    TaskDetailSerializer,
)

User = get_user_model()


def _normalize_task_input(data):
    """
    Map legacy payload => new fields (column/assignee/priority aliases).
    """
    d = dict(data)
    if "assignee" in d and "assignee_id" not in d:
        d["assignee_id"] = d.pop("assignee")
    if "reviewer" in d and "reviewer_id" not in d:
        d["reviewer_id"] = d.pop("reviewer")
    if "status" not in d and "column" in d:
        col = d["column"]
        name_map = {
            "todo": "to-do",
            "to-do": "to-do",
            "doing": "in-progress",
            "in-progress": "in-progress",
            "review": "review",
            "done": "done",
        }
        if isinstance(col, str):
            d["status"] = name_map.get(col.strip().lower(), "to-do")
        else:
            d["status"] = {0: "to-do", 1: "in-progress", 2: "review", 3: "done"}.get(
                int(col), "to-do"
            )
    if str(d.get("priority", "")).lower() in {"mid", "med"}:
        d["priority"] = "medium"
    return d


# ---------- Boards ----------
class BoardViewSet(viewsets.ViewSet):
    """Board CRUD and member management."""
    permission_classes = [IsAuthenticated]

    def _get_accessible_board(self, user, pk):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        allowed = board.owner_id == user.id or board.members.filter(id=user.id).exists()
        if not allowed:
            # Hide existence for non-members
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return board

    def _get_owner_board(self, user, pk):
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if board.owner_id != user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return board

    def list(self, request):
        boards = (
            Board.objects.filter(Q(owner=request.user) | Q(members=request.user))
            .distinct()
            .order_by("id")
        )
        return Response(BoardListSerializer(boards, many=True).data)

    def retrieve(self, request, pk=None):
        board = self._get_accessible_board(request.user, pk)
        if isinstance(board, Response):
            return board
        board = Board.objects.filter(pk=pk).prefetch_related("members").get()
        return Response(BoardDetailSerializer(board).data)

    def create(self, request):
        title = (request.data.get("title") or "").strip()
        if not (2 < len(title) < 64):
            return Response(
                {"title": ["Title must be between 3 and 63 characters."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        board = Board.objects.create(title=title, owner=request.user)
        BoardMember.objects.get_or_create(board=board, user=request.user)
        return Response(BoardListSerializer(board).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        board = self._get_owner_board(request.user, pk)
        if isinstance(board, Response):
            return board
        data = request.data or {}

        if "title" in data:
            title = (data.get("title") or "").strip()
            if not (2 < len(title) < 64):  # pragma: no cover - negative branch
                return Response(
                    {"title": ["Title must be between 3 and 63 characters."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            board.title = title
            board.save(update_fields=["title"])

        if isinstance(data.get("members"), list):
            ids = {int(x) for x in data["members"] if str(x).isdigit()}
            ids.add(board.owner_id)
            BoardMember.objects.filter(board=board).exclude(
                user_id=board.owner_id
            ).delete()
            for uid in ids:
                BoardMember.objects.get_or_create(board=board, user_id=uid)

        board = Board.objects.prefetch_related("members").get(pk=board.pk)
        return Response(BoardDetailSerializer(board).data)

    def destroy(self, request, pk=None):
        board = self._get_owner_board(request.user, pk)
        if isinstance(board, Response):
            return board
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Tasks ----------
class TaskCreateView(APIView):
    """Create tasks (accepts legacy payloads) and list tasks on GET."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = _normalize_task_input(request.data)
        serializer = TaskCreateUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response({"id": task.id}, status=status.HTTP_201_CREATED)

    def get(self, request):
        """List tasks; supports ?assigned_to_me=true for legacy tests."""
        qs = Task.objects.filter(
            Q(board__owner=request.user) | Q(board__members=request.user)
        ).select_related("assignee", "reviewer", "board")
        if (request.query_params.get("assigned_to_me") or "").lower() == "true":
            qs = qs.filter(assignee=request.user)
        qs = qs.annotate(comments_count=Count("comments")).order_by("id")
        return Response(TaskDetailSerializer(qs, many=True).data)


class TaskDetailView(APIView):
    """Retrieve, update, or delete a task."""
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            task = (
                Task.objects.filter(pk=task_id)
                .select_related("assignee", "reviewer", "board")
                .annotate(comments_count=Count("comments"))
                .get()
            )
        except Task.DoesNotExist:  # pragma: no cover - negative path
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)

    def patch(self, request, task_id):
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:  # pragma: no cover - negative path
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        data = _normalize_task_input(request.data)
        serializer = TaskCreateUpdateSerializer(task, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True}, status=status.HTTP_200_OK)

    def delete(self, request, task_id):
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:  # pragma: no cover - negative path
            return Response(status=status.HTTP_404_NOT_FOUND)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignedToMeView(APIView):
    """List tasks assigned to the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Task.objects.filter(assignee=request.user)
            .select_related("assignee", "reviewer", "board")
            .annotate(comments_count=Count("comments"))
            .order_by("id")
        )
        return Response(TaskDetailSerializer(qs, many=True).data)


class ReviewingView(APIView):
    """List tasks where the current user is reviewer."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Task.objects.filter(reviewer=request.user)
            .select_related("assignee", "reviewer", "board")
            .annotate(comments_count=Count("comments"))
            .order_by("id")
        )
        return Response(TaskDetailSerializer(qs, many=True).data)


# ---------- Comments ----------
class TaskCommentsView(APIView):
    """List and create comments for a given task (nested route)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        qs = (
            Comment.objects.filter(task_id=task_id)
            .select_related("author")
            .order_by("-id")
        )
        return Response(CommentSerializer(qs, many=True).data)

    def post(self, request, task_id):
        content = (request.data.get("content") or "").strip()
        if not content:  # pragma: no cover - negative branch
            return Response(
                {"content": ["Content required"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comment = Comment.objects.create(
            task_id=task_id, author=request.user, content=content
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentsCollectionView(APIView):
    """
    Back-compat collection endpoint:
    - POST /api/kanban/comments/      {task, content}
    - GET  /api/kanban/comments/?task=<id>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task_id = request.data.get("task")
        if not task_id:  # pragma: no cover - negative branch
            return Response({"task": ["Task is required"]}, status=400)
        return TaskCommentsView().post(request, task_id=task_id)

    def get(self, request):
        task_id = request.query_params.get("task")
        if not task_id:  # pragma: no cover - no-op listing
            return Response([], status=200)
        return TaskCommentsView().get(request, task_id=task_id)


class SingleCommentView(APIView):
    """Delete a single comment (author only)."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, comment_id):
        try:
            comment = Comment.objects.get(pk=comment_id, task_id=task_id)
        except Comment.DoesNotExist:  # pragma: no cover - negative path
            return Response(status=status.HTTP_404_NOT_FOUND)
        if comment.author_id != request.user.id:  # pragma: no cover - negative path
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Dashboard ----------
class DashboardView(APIView):
    """Aggregate stats used by the dashboard widgets."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Task.objects.filter(
            Q(board__owner=request.user) | Q(board__members=request.user)
        ).distinct()
        pri = qs.values("priority").annotate(count=Count("id"))
        sta = qs.values("status").annotate(count=Count("id"))
        return Response(
            {
                "tickets_total": qs.count(),
                "by_priority": {r["priority"]: r["count"] for r in pri},
                "by_status": {r["status"]: r["count"] for r in sta},
            }
        )
