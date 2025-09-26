"""
URL configuration for the Kanban API.
Defines all REST endpoints for boards, tasks, and comments.
Each path maps to a corresponding view for CRUD operations.
"""
from django.urls import path

from .views import (
    BoardsCollectionView,
    BoardDetailView,
    TasksCollectionView,
    TaskDetailView,
    TasksAssignedToMeView,
    TasksReviewingView,
    CommentsCollectionView,
    CommentDeleteView,
)

urlpatterns = [
    # ---------- Boards ----------
    # List all boards or create a new board
    path("boards/", BoardsCollectionView.as_view(), name="boards-collection"),
    # Retrieve, update, or delete a specific board by ID
    path("boards/<int:board_id>/", BoardDetailView.as_view(), name="board-detail"),

    # ---------- Tasks ----------
    # List all tasks or create a new task
    path("tasks/", TasksCollectionView.as_view(), name="tasks-collection"),
    # Retrieve, update, or delete a specific task by ID
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
    # List tasks assigned to the currently authenticated user
    path("tasks/assigned-to-me/", TasksAssignedToMeView.as_view(), name="tasks-assigned"),
    # List tasks where the current user is the reviewer
    path("tasks/reviewing/", TasksReviewingView.as_view(), name="tasks-reviewing"),

    # ---------- Comments ----------
    # List all comments for a task or create a new comment
    path(
        "tasks/<int:task_id>/comments/",
        CommentsCollectionView.as_view(),
        name="comments-collection",
    ),
    # Delete a specific comment on a task by ID
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        CommentDeleteView.as_view(),
        name="comment-delete",
    ),
]
