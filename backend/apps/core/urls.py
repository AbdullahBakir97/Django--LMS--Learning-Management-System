from django.urls import path

from .views import HealthView, RealtimeTicketView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("realtime/ticket/", RealtimeTicketView.as_view(), name="realtime-ticket"),
]
