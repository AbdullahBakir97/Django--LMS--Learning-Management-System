from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, PreferenceView

router = DefaultRouter()
router.include_root_view = False
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("notifications/preferences/", PreferenceView.as_view(), name="notification-preferences"),
    path("", include(router.urls)),
]
