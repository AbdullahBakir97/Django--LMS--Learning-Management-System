from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register("groups", views.GroupViewSet, basename="group")
router.register("posts", views.PostViewSet, basename="post")
router.register("events", views.EventViewSet, basename="event")

urlpatterns = [
    path(
        "groups/<slug:slug>/members/<int:user_id>/approve/",
        views.MemberView.as_view(http_method_names=["post"]),
        name="group-member-approve",
    ),
    path(
        "groups/<slug:slug>/members/<int:user_id>/",
        views.MemberView.as_view(http_method_names=["patch", "delete"]),
        name="group-member",
    ),
    path("", include(router.urls)),
]
