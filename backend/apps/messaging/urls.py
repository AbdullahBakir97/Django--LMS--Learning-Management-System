from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register("conversations", views.ConversationViewSet, basename="conversation")

urlpatterns = [
    path("conversations/<int:pk>/messages/", views.MessagesView.as_view(), name="messages"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message-detail"),
    path("", include(router.urls)),
]
