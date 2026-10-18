from django.urls import path

from . import views

urlpatterns = [
    path("payments/checkout/", views.CheckoutView.as_view(), name="payments-checkout"),
    path(
        "payments/courses/<slug:slug>/revenue/",
        views.CourseRevenueView.as_view(),
        name="payments-course-revenue",
    ),
    path("payments/webhook/", views.WebhookView.as_view(), name="payments-webhook"),
]
