from django.urls import path

from . import views

urlpatterns = [path("insights/overview/", views.OverviewView.as_view(), name="insights-overview")]
