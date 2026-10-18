from django.urls import path

from . import views

urlpatterns = [
    path("reports/", views.ReportView.as_view(), name="report"),
    path("moderation/queue/", views.QueueView.as_view(), name="moderation-queue"),
    path(
        "moderation/<str:kind>/<int:object_id>/resolve/",
        views.ResolveView.as_view(),
        name="moderation-resolve",
    ),
]
