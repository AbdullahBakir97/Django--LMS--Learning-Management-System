from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('roomId', 'name', 'created_at')
    search_fields = ('roomId', 'name')
    filter_horizontal = ('members',)  # Allows for easier selection of members

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat', 'content', 'timestamp', 'is_read')
    list_filter = ('chat', 'sender', 'timestamp', 'is_read', 'message_type')
    search_fields = ('sender__username', 'chat__roomId', 'content')
    date_hierarchy = 'timestamp'
    filter_horizontal = ('attachments', 'reactions', 'shares')  # Allows for easier selection of related objects
    raw_id_fields = ('parent_message',)  # Provides a raw ID field for parent_message for efficient lookup

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('sender', 'chat')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'sender':
            kwargs['queryset'] = db_field.remote_field.model.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ('attachments', 'reactions', 'shares'):
            kwargs['queryset'] = db_field.remote_field.model.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Custom logic or actions after saving related objects

admin.site.site_header = 'LMS Administration'  # Customize admin site header
