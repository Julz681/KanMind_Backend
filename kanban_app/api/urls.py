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
    # Boards
    path("boards/", BoardsCollectionView.as_view(), name="boards-collection"),
    path("boards/<int:board_id>/", BoardDetailView.as_view(), name="board-detail"),

    # Tasks
    path("tasks/", TasksCollectionView.as_view(), name="tasks-collection"),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/assigned-to-me/", TasksAssignedToMeView.as_view(), name="tasks-assigned"),
    path("tasks/reviewing/", TasksReviewingView.as_view(), name="tasks-reviewing"),

    # Comments
    path("tasks/<int:task_id>/comments/", CommentsCollectionView.as_view(), name="comments-collection"),
    path("tasks/<int:task_id>/comments/<int:comment_id>/", CommentDeleteView.as_view(), name="comment-delete"),
]
