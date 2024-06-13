from django.contrib import admin
from .models import Event
from profiles.models import UserProfile
from activity.models import Attachment, Category
from django.contrib.contenttypes.admin import GenericTabularInline

# Inline for GenericRelation Attachment
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'location', 'start_time', 'end_time', 'get_attendees_count')
    list_filter = ('organizer', 'location', 'start_time', 'end_time', 'event_date')
    search_fields = ('title', 'organizer__user__username', 'location')

    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'organizer', 'attachments', 'categories', 'location', 'start_time', 'end_time', 'event_date', 'capacity', 'category')
        }),
    )

    filter_horizontal = ('categories', 'attendees')
    inlines = [AttachmentInline]

    def get_attendees_count(self, obj):
        """Custom method to display number of attendees."""
        return obj.attendees.count()
    get_attendees_count.short_description = 'Attendees'

    def save_model(self, request, obj, form, change):
        """Override save_model to associate the current user with the Event."""
        if not obj.pk:
            obj.organizer = UserProfile.objects.get(user=request.user)
        obj.save()

# Register models
admin.site.register(UserProfile)
