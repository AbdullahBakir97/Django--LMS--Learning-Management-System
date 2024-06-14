from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Category, Share, Reaction, Attachment, Thread, UserActivity, UserStatistics, MarketingCampaign, LearningService, Analytics

# Inline for GenericRelation Attachment
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

# Admin classes for each model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)



@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('user', 'shared_at', 'content_object')
    list_filter = ('user', 'shared_at')
    search_fields = ('user__username', 'shared_to__username', 'content_object__name')

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'user', 'get_content_object', 'message', 'post', 'comment', 'job_post', 'group')
    list_filter = ('type', 'user')
    search_fields = ('user__username',)

    def get_content_object(self, obj):
        return obj.content_object

    get_content_object.short_description = 'Content Object'  # Customize the column header
    get_content_object.admin_order_field = 'content_object__id'  # Optionally, enable sorting by content object ID

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('attachment_type', 'uploaded_at', 'content_object')
    list_filter = ('attachment_type', 'uploaded_at')
    search_fields = ('content_object__name',)
    inlines = [AttachmentInline]

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'last_message_at')
    list_filter = ('last_message_at',)
    search_fields = ('subject',)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username',)

@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'connections_count', 'posts_count', 'engagement_rate')
    list_filter = ('connections_count', 'posts_count', 'engagement_rate')
    search_fields = ('user__username',)

@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ('campaign_name', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('campaign_name',)

@admin.register(LearningService)
class LearningServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'resources')
    search_fields = ('service_name',)

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'engagement_rate')
    search_fields = ('activity_type', 'engagement_rate')
