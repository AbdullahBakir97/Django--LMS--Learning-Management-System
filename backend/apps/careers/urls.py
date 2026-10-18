from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register("companies", views.CompanyViewSet, basename="company")
router.register("jobs", views.JobViewSet, basename="job")
router.register("applications", views.ApplicationViewSet, basename="application")
router.register("interviews", views.InterviewViewSet, basename="interview")
router.register("company-updates", views.CompanyUpdateViewSet, basename="company-update")

urlpatterns = [
    path(
        "companies/<slug:slug>/members/<int:user_id>/",
        views.CompanyMemberView.as_view(),
        name="company-member",
    ),
    path("", include(router.urls)),
]
