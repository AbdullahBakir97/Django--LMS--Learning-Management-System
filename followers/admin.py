from django.contrib import admin
from .models import Follower, FollowRequest, FollowNotification
from django.conf import settings
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils import timezone

# Inline for GenericRelation Attachment
class FollowerInline(admin.TabularInline):
    model = Follower
    extra = 1
    readonly_fields = ('followed_at',)

class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__user__username', 'to_user__user__username')

    def save_model(self, request, obj, form, change):
        """Override save_model to send notification on request acceptance."""
        if obj.status == 'accepted':
            notification_message = f"{obj.from_user.user.username} started following you."
            FollowNotification.objects.create(user=obj.to_user, message=notification_message)
        obj.save()

@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ('user', 'follower', 'followed_at')
    list_filter = ('followed_at',)
    search_fields = ('user__user__username', 'follower__user__username')

    def save_model(self, request, obj, form, change):
        """Override save_model to send notification on new follower."""
        if not obj.pk:  # If new follower
            notification_message = f"{obj.follower.user.username} started following you."
            FollowNotification.objects.create(user=obj.user, message=notification_message)
        obj.save()

@admin.register(FollowNotification)
class FollowNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__user__username', 'message')

# Register models
admin.site.register(FollowRequest, FollowRequestAdmin)
