"""
Views für Kanban-API gemäß Dokumentation.
Achtet auf exakte Antwortformate und korrekte Berechtigungen.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from kanban_app.models import Board, Task, Comment
from .serializers import (
    UserMiniSerializer,
    BoardListItemSerializer,
    BoardCreateSerializer,
    BoardCreateResponseSerializer,
    BoardDetailSerializer,
    BoardMemberSerializer,
    TaskOnBoardSerializer,
    BoardUpdateSerializer,
    BoardUpdateResponseSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
)

User = get_user_model()

# ---------- Hilfsfunktionen ----------

def is_board_member_or_owner(board: Board, user) -> bool:
    return board.owner_id == user.id or board.members.filter(id=user.id).exists()

def forbid_403():
    return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

def ensure_board_member(board: Board, user):
    if not is_board_member_or_owner(board, user):
        return forbid_403()
    return None

def ensure_board_owner(board: Board, user):
    if board.owner_id != user.id:
        return forbid_403()
    return None

def serialize_task_for_board(task: Task):
    task.comments_count = task.comments.count()
    return TaskOnBoardSerializer(task).data

def serialize_task_detail(task: Task):
    task.comments_count = task.comments.count()
    return TaskDetailSerializer(task).data


# ---------- Boards ----------

class BoardsCollectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        boards = Board.objects.filter(Q(owner_id=user.id) | Q(members__id=user.id)).distinct()

        items = []
        for b in boards:
            tasks_qs = Task.objects.filter(board=b)
            items.append({
                "id": b.id,
                "title": b.title,
                "member_count": b.members.count(),
                "ticket_count": tasks_qs.count(),
                "tasks_to_do_count": tasks_qs.filter(status="to-do").count(),
                "tasks_high_prio_count": tasks_qs.filter(priority="high").count(),
                "owner_id": b.owner_id,
            })

        return Response(BoardListItemSerializer(items, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        ser = BoardCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        board = Board.objects.create(title=ser.validated_data["title"].strip(), owner=user)

        member_ids = ser.validated_data["members"]
        if member_ids:
            users = User.objects.filter(id__in=member_ids)
            board.members.add(*users)

        tasks_qs = Task.objects.filter(board=board)
        resp = {
            "id": board.id,
            "title": board.title,
            "member_count": board.members.count(),
            "ticket_count": tasks_qs.count(),
            "tasks_to_do_count": tasks_qs.filter(status="to-do").count(),
            "tasks_high_prio_count": tasks_qs.filter(priority="high").count(),
            "owner_id": board.owner_id,
        }
        return Response(BoardCreateResponseSerializer(resp).data, status=status.HTTP_201_CREATED)


class BoardDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, board_id: int):
        board = get_object_or_404(Board, id=board_id)
        forbid = ensure_board_member(board, request.user)
        if forbid:
            return forbid

        members = board.members.all().order_by("id")
        tasks = Task.objects.filter(board=board).select_related("assignee", "reviewer")

        payload = {
            "id": board.id,
            "title": board.title,
            "owner_id": board.owner_id,
            "members": BoardMemberSerializer(members, many=True).data,
            "tasks": [serialize_task_for_board(t) for t in tasks],
        }
        return Response(BoardDetailSerializer(payload).data, status=status.HTTP_200_OK)

    def patch(self, request, board_id: int):
        board = get_object_or_404(Board, id=board_id)
        forbid = ensure_board_member(board, request.user)  # laut Doku: Owner ODER Member
        if forbid:
            return forbid

        ser = BoardUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        if "title" in ser.validated_data:
            board.title = ser.validated_data["title"].strip()
            board.save(update_fields=["title"])

        if "members" in ser.validated_data:
            users = User.objects.filter(id__in=ser.validated_data["members"])
            board.members.set(users)

        payload = {
            "id": board.id,
            "title": board.title,
            "owner_data": UserMiniSerializer(board.owner).data,
            "members_data": UserMiniSerializer(board.members.all(), many=True).data,
        }
        return Response(BoardUpdateResponseSerializer(payload).data, status=status.HTTP_200_OK)

    def delete(self, request, board_id: int):
        board = get_object_or_404(Board, id=board_id)
        forbid = ensure_board_owner(board, request.user)  # nur Owner
        if forbid:
            return forbid
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Tasks ----------

class TasksCollectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Hilfs-Liste (nicht in der Doku, aber praktisch): alle Tasks auf zugänglichen Boards
        user = request.user
        board_ids = Board.objects.filter(Q(owner_id=user.id) | Q(members__id=user.id)).values_list("id", flat=True)
        tasks = Task.objects.filter(board_id__in=board_ids).select_related("assignee", "reviewer")
        return Response([serialize_task_detail(t) for t in tasks], status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        ser = TaskCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        board = get_object_or_404(Board, id=ser.validated_data["board"])
        forbid = ensure_board_member(board, user)
        if forbid:
            return forbid

        def resolve_user(optional_id):
            if optional_id in (None, "",):
                return None
            u = get_object_or_404(User, id=optional_id)
            if not is_board_member_or_owner(board, u):
                # muss Mitglied/Owner sein
                raise ValueError("assignee/reviewer muss Board-Mitglied sein.")
            return u

        try:
            assignee = resolve_user(ser.validated_data.get("assignee_id"))
            reviewer = resolve_user(ser.validated_data.get("reviewer_id"))
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # --- WICHTIG: created_by nur setzen, wenn Feld existiert (verhindert 500) ---
        kwargs = dict(
            board=board,
            title=ser.validated_data["title"].strip(),
            description=ser.validated_data.get("description", "").strip(),
            status=ser.validated_data["status"],
            priority=ser.validated_data["priority"],
            assignee=assignee,
            reviewer=reviewer,
            due_date=ser.validated_data.get("due_date"),
        )
        if hasattr(Task, "created_by"):
            kwargs["created_by"] = user

        task = Task.objects.create(**kwargs)
        return Response(serialize_task_detail(task), status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, task_id: int):
        task = get_object_or_404(Task.objects.select_related("board"), id=task_id)
        forbid = ensure_board_member(task.board, request.user)
        if forbid:
            return forbid

        ser = TaskUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        if "title" in ser.validated_data:
            task.title = ser.validated_data["title"].strip()
        if "description" in ser.validated_data:
            task.description = ser.validated_data["description"]
        if "status" in ser.validated_data:
            task.status = ser.validated_data["status"]
        if "priority" in ser.validated_data:
            task.priority = ser.validated_data["priority"]
        if "due_date" in ser.validated_data:
            task.due_date = ser.validated_data["due_date"]

        def resolve_user(optional_id):
            if optional_id in (None, "",):
                return None
            u = get_object_or_404(User, id=optional_id)
            if not is_board_member_or_owner(task.board, u):
                raise ValueError("assignee/reviewer muss Board-Mitglied sein.")
            return u

        try:
            if "assignee_id" in ser.validated_data:
                task.assignee = resolve_user(ser.validated_data["assignee_id"])
            if "reviewer_id" in ser.validated_data:
                task.reviewer = resolve_user(ser.validated_data["reviewer_id"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        task.save()
        return Response(serialize_task_detail(task), status=status.HTTP_200_OK)

    def delete(self, request, task_id: int):
        task = get_object_or_404(Task.objects.select_related("board"), id=task_id)
        board = task.board
        allowed = (board.owner_id == request.user.id)
        if hasattr(task, "created_by") and task.created_by_id == request.user.id:
            allowed = True
        if not allowed:
            return forbid_403()
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Filter-Views (aus Doku) ----------

class TasksAssignedToMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assignee=request.user).select_related("assignee", "reviewer")
        return Response([serialize_task_detail(t) for t in tasks], status=status.HTTP_200_OK)


class TasksReviewingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(reviewer=request.user).select_related("assignee", "reviewer")
        return Response([serialize_task_detail(t) for t in tasks], status=status.HTTP_200_OK)


# ---------- Comments ----------

class CommentsCollectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id: int):
        task = get_object_or_404(Task.objects.select_related("board"), id=task_id)
        forbid = ensure_board_member(task.board, request.user)
        if forbid:
            return forbid
        comments = task.comments.all().order_by("id")
        return Response(CommentSerializer(comments, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, task_id: int):
        task = get_object_or_404(Task.objects.select_related("board"), id=task_id)
        forbid = ensure_board_member(task.board, request.user)
        if forbid:
            return forbid

        ser = CommentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        c = Comment.objects.create(task=task, author=request.user, content=ser.validated_data["content"])
        return Response(CommentSerializer(c).data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, task_id: int, comment_id: int):
        task = get_object_or_404(Task.objects.select_related("board"), id=task_id)
        forbid = ensure_board_member(task.board, request.user)
        if forbid:
            return forbid
        comment = get_object_or_404(Comment, id=comment_id, task=task)
        if comment.author_id != request.user.id:
            return forbid_403()
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
