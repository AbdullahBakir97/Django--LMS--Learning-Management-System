from django.contrib import admin

from .models import Notification, Preference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "kind", "title", "read_at", "created_at"]
    list_filter = ["kind"]
    search_fields = ["title", "recipient__email"]
    raw_id_fields = ["recipient", "actor"]


admin.site.register(Preference)
