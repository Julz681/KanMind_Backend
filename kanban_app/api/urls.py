"""
URL configuration for the Kanban API.

Provides endpoints for:
- Boards (CRUD)
- Tasks (create, list, detail, assigned-to-me, reviewing)
- Task comments (list, create, detail)
- Comments collection (legacy)
- Dashboard (aggregates)
"""

from django.urls import path
from .views import (
    AssignedToMeView,
    BoardViewSet,
    ReviewingView,
    SingleCommentView,
    TaskCommentsView,
    TaskCreateView,
    TaskDetailView,
    CommentsCollectionView,
    DashboardView,
)

board_list = BoardViewSet.as_view({"get": "list", "post": "create"})
board_detail = BoardViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    # Boards
    path("boards/", board_list, name="boards-list"),
    path("boards/<int:pk>/", board_detail, name="boards-detail"),

    # Tasks
    path("tasks/assigned-to-me/", AssignedToMeView.as_view(), name="tasks-assigned"),
    path("tasks/reviewing/", ReviewingView.as_view(), name="tasks-reviewing"),
    path("tasks/", TaskCreateView.as_view(), name="tasks-create-or-list"),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="tasks-detail"),

    # Comments (nested)
    path("tasks/<int:task_id>/comments/", TaskCommentsView.as_view(), name="task-comments"),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        SingleCommentView.as_view(),
        name="task-comment-detail",
    ),

    # Comments collection (legacy endpoints)
    path("comments/", CommentsCollectionView.as_view(), name="comments-collection"),

    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
