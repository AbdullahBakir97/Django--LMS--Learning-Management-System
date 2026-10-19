from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "course", "amount_cents", "currency", "status", "paid_at")
    list_filter = ("status", "currency")
    search_fields = ("buyer__username", "course__title", "checkout_session")
    readonly_fields = [f.name for f in Order._meta.fields]
