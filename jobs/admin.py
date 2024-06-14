from django.contrib import admin
from django import forms
from taggit.forms import TagWidget
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import JobListing, JobApplication, JobNotification
from activity.models import Attachment

# Inline for Attachments
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

# Custom Admin Form for JobListing
class JobListingAdminForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = '__all__'
        widgets = {
            'tags': TagWidget,
        }

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    form = JobListingAdminForm
    list_display = ('title', 'company', 'location', 'posted_date', 'closing_date', 'is_active')
    list_filter = ('company', 'location', 'posted_date', 'closing_date', 'is_active', 'categories')
    search_fields = ('title', 'description', 'location', 'requirements', 'responsibilities')
    readonly_fields = ('posted_date',)
    inlines = (AttachmentInline,)
    filter_horizontal = ('categories', 'skills_required', 'shares')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job_listing', 'status', 'applied_date')
    list_filter = ('job_listing', 'status', 'applied_date')
    search_fields = ('applicant__username', 'job_listing__title')
    readonly_fields = ('applied_date',)
    filter_horizontal = ('shares',)

@admin.register(JobNotification)
class JobNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_listing', 'created_at', 'read')
    list_filter = ('job_listing', 'created_at', 'read')
    search_fields = ('user__username', 'job_listing__title')
    readonly_fields = ('created_at',)
    filter_horizontal = ('shares',)
