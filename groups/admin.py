from django.contrib import admin
from .models import Group, GroupMembership
from django.conf import settings
from django.utils.html import format_html
from activity.models import Share, Category

# Inline for GroupMembership
class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1
    readonly_fields = ('joined_at',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_summary', 'group_type', 'privacy_level', 'created_at')
    list_filter = ('group_type', 'privacy_level', 'categories')
    search_fields = ('name', 'description')

    def description_summary(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_summary.short_description = 'Description'

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__user__username', 'group__name')

