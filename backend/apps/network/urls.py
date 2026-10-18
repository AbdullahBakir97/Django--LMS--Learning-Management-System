from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register("connections", views.ConnectionViewSet, basename="connection")

urlpatterns = [
    path("network/suggestions/", views.SuggestionsView.as_view(), name="network-suggestions"),
    path("network/<str:username>/", views.RelationshipView.as_view(), name="relationship"),
    path("network/<str:username>/follow/", views.FollowView.as_view(), name="follow"),
    path("network/<str:username>/followers/", views.FollowersView.as_view(), name="followers"),
    path("network/<str:username>/following/", views.FollowingView.as_view(), name="following"),
    path(
        "network/<str:username>/recommendations/",
        views.RecommendationsView.as_view(),
        name="recommendations",
    ),
    path(
        "network/<str:username>/recommendations/request/",
        views.RecommendationRequestView.as_view(),
        name="recommendation-request",
    ),
    path(
        "recommendations/<int:pk>/",
        views.RecommendationDetailView.as_view(),
        name="recommendation-detail",
    ),
    path("", include(router.urls)),
]
