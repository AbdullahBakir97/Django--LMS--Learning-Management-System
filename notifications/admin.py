from django.contrib import admin
from .models import Notification, NotificationTemplate, NotificationSettings, NotificationReadStatus, NotificationType
from .forms import NotificationTypeForm
@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    form = NotificationTypeForm
    list_display = ('type_name',)
    search_fields = ('type_name',)

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('notification_type',)
    search_fields = ('notification_type__type_name',)

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_enabled')
    list_filter = ('notification_type', 'is_enabled')
    search_fields = ('user__username', 'notification_type__type_name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('notification_type', 'is_read', 'timestamp')
    search_fields = ('recipient__user__username', 'notification_type__type_name')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'

@admin.register(NotificationReadStatus)
class NotificationReadStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'is_read', 'read_at')
    list_filter = ('is_read',)
    search_fields = ('user__user__username', 'notification__notification_type__type_name')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'notification')

    def notification_type(self, obj):
        return obj.notification.notification_type.type_name

    notification_type.short_description = 'Notification Type'
