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
            'fields': ('title', 'description', 'organizer', 'categories', 'location', 'start_time', 'end_time', 'event_date', 'capacity', 'category')
        }),
    )

    filter_horizontal = ('categories', 'attendees')
    inlines = [AttachmentInline]

    readonly_fields = ('get_attendees_count',)  # Assuming this is a readonly method

    def get_attendees_count(self, obj):
        """Custom method to display number of attendees."""
        return obj.attendees.count()
    get_attendees_count.short_description = 'Attendees'

    def save_model(self, request, obj, form, change):
        """Override save_model to associate the current user with the Event."""
        if not obj.pk:  # Only set organizer on creation
            obj.organizer = UserProfile.objects.get(user=request.user)
        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        """Override get_form to exclude attachments field."""
        form = super().get_form(request, obj, **kwargs)
        if 'attachments' in form.base_fields:
            del form.base_fields['attachments']
        return form

    def get_inline_instances(self, request, obj=None):
        """Override get_inline_instances to pass request to inlines."""
        inline_instances = []
        for inline_class in self.inlines:
            inline = inline_class(self.model, self.admin_site)
            if request:
                inline.request = request
            inline_instances.append(inline)
        return inline_instances
