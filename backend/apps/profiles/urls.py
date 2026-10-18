from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("profiles/me/experiences", views.ExperienceViewSet, basename="my-experiences")
router.register("profiles/me/educations", views.EducationViewSet, basename="my-educations")
router.register("profiles/me/portfolio", views.PortfolioItemViewSet, basename="my-portfolio")
router.register("profiles/me/skills", views.ProfileSkillViewSet, basename="my-skills")

urlpatterns = [
    path("profiles/me/", views.MyProfileView.as_view(), name="my-profile"),
    path("profiles/<str:username>/", views.ProfileDetailView.as_view(), name="profile-detail"),
    path(
        "profiles/<str:username>/skills/<int:pk>/endorse/",
        views.EndorseView.as_view(),
        name="skill-endorse",
    ),
    path("skills/", views.SkillSearchView.as_view(), name="skill-search"),
    *router.urls,
]
