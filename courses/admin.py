from django.contrib import admin
from .models import Course, CourseEnrollment, CourseCompletion
from django.contrib.contenttypes.admin import GenericTabularInline
from posts.models import Comment
from certifications.models import Certification
from activity.models import Attachment

# Inline for GenericRelation Attachment
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

# Inline for CourseEnrollment in UserProfileAdmin
class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
    extra = 1
    readonly_fields = ('enrolled_at',)

# Inline for CourseCompletion in UserProfileAdmin
class CourseCompletionInline(admin.TabularInline):
    model = CourseCompletion
    extra = 1
    readonly_fields = ('completed_at',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'get_students_count', 'get_completions_count')
    list_filter = ('instructor', 'categories')
    search_fields = ('title', 'instructor__username')

    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'description', 'instructor', 'attachments', 'categories', 'tags')
        }),
        ('Related Content', {
            'fields': ('shares', 'comments', 'reactions')
        }),
    )

    filter_horizontal = ('categories', 'tags')
    inlines = [AttachmentInline, CourseEnrollmentInline, CourseCompletionInline]

    def get_queryset(self, request):
        """Limit queryset to current user's instructed courses."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(instructor=request.user)
        return qs

    def get_students_count(self, obj):
        """Custom method to display number of enrolled students."""
        return obj.students.count()
    get_students_count.short_description = 'Students'

    def get_completions_count(self, obj):
        """Custom method to display number of course completions."""
        return obj.completions.count()
    get_completions_count.short_description = 'Completions'

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'enrolled_at')
    list_filter = ('enrolled_at',)
    search_fields = ('course__title', 'student__user__username')

@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'completed_at', 'certificate_url', 'certificate')
    list_filter = ('completed_at',)
    search_fields = ('course__title', 'student__user__username')

# Register models
admin.site.register(Comment)
admin.site.register(Certification)
