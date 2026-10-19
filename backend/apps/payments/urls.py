from django.urls import path

from . import views

urlpatterns = [
    path("payments/checkout/", views.CheckoutView.as_view(), name="payments-checkout"),
    path("payments/webhook/", views.WebhookView.as_view(), name="payments-webhook"),
]
