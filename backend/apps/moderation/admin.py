from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("kind", "object_id", "reason", "status", "reporter", "created_at")
    list_filter = ("status", "kind", "reason")
    search_fields = ("reporter__username", "details")
