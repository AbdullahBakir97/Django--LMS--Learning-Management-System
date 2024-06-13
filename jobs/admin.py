from django.contrib import admin
from .models import JobListing, JobApplication, JobNotification
from django.contrib.contenttypes.admin import GenericTabularInline
from activity.models import Attachment
from django.urls import reverse
from django.utils.safestring import mark_safe

# Inline for Attachments
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_date', 'closing_date', 'is_active')
    list_filter = ('company', 'location', 'posted_date', 'closing_date', 'is_active', 'categories')
    search_fields = ('title', 'description', 'location', 'requirements', 'responsibilities')
    readonly_fields = ('posted_date',)
    inlines = (AttachmentInline,)
    filter_horizontal = ('categories', 'skills_required', 'shares', 'tags')

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
