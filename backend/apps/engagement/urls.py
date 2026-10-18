from django.urls import path

from . import views

urlpatterns = [
    path(
        "engagement/<slug:key>/<int:pk>/comments/",
        views.CommentsView.as_view(),
        name="comments",
    ),
    path(
        "engagement/<slug:key>/<int:pk>/reactions/",
        views.ReactionsView.as_view(),
        name="reactions",
    ),
    path("comments/<int:pk>/", views.CommentDetailView.as_view(), name="comment-detail"),
]
