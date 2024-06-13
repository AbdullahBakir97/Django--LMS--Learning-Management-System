from django.contrib import admin
from .models import Post, Comment
from activity.models import Attachment
from django.contrib.contenttypes.admin import GenericTabularInline

# Inline for GenericRelation Attachment
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1
    
    
# Inline for replies (child comments)
class ReplyInline(admin.TabularInline):  # or admin.StackedInline if you prefer
    model = Comment
    fk_name = 'parent_comment'
    fields = ('author', 'content', 'visibility', 'created_at')  # Adjust fields as necessary
    readonly_fields = ('created_at',)
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        # Override get_formset to set the parent comment dynamically
        formset = super().get_formset(request, obj, **kwargs)
        formset.parent_obj = obj  # Store the parent comment object in the formset
        return formset

    def get_queryset(self, request):
        # Override get_queryset to filter only direct replies to the current comment
        queryset = super().get_queryset(request)
        parent_obj = getattr(self.formset, 'parent_obj', None)
        if parent_obj:
            return queryset.filter(parent_comment=parent_obj)
        else:
            return queryset.none()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content_preview', 'group', 'visibility', 'created_at')
    list_filter = ('visibility', 'created_at', 'author')
    search_fields = ('content', 'author__username', 'group__name')
    date_hierarchy = 'created_at'
    filter_horizontal = ('categories', 'likes', 'reactions', 'comments', 'shares', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('author', 'group', 'content', 'visibility', 'categories')
        }),
        ('Advanced Options', {
            'fields': ('likes', 'reactions', 'comments', 'shares', 'tags'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    inlines = [AttachmentInline]

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'content_preview', 'visibility', 'created_at')
    list_filter = ('visibility', 'created_at', 'author')
    search_fields = ('content', 'author__username', 'post__content')
    date_hierarchy = 'created_at'
    filter_horizontal = ('reactions',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('post', 'author', 'content', 'visibility')
        }),
        ('Advanced Options', {
            'fields': ('reactions',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    inlines = [AttachmentInline, ReplyInline]  # Include ReplyInline here

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'