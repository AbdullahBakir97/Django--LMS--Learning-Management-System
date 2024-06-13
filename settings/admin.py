from django.contrib import admin
from .models import SettingType, UserSetting, GlobalSetting
from profiles.models import UserProfile

@admin.register(SettingType)
class SettingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    list_per_page = 20
    ordering = ('name',)

@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'setting_type', 'value')
    list_filter = ('setting_type',)
    search_fields = ('user__user__username', 'setting_type__name')
    list_per_page = 20
    autocomplete_fields = ['user']
    ordering = ('user__user__username', 'setting_type__name')

@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ('setting_type', 'value')
    search_fields = ('setting_type__name',)
    list_per_page = 20
    ordering = ('setting_type__name',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
