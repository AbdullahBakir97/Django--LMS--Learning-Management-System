from django.contrib import admin
from .models import Company, CompanyUpdate
from activity.models import Category, Attachment
from django.contrib.contenttypes.admin import GenericTabularInline

# Inline for GenericRelation Attachment
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1

# Inline for Company Updates
class CompanyUpdateInline(admin.TabularInline):
    model = CompanyUpdate
    extra = 1
    fields = ('title', 'content', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'location', 'industry', 'founded_date', 'employee_count')
    list_filter = ('industry', 'founded_date', 'employee_count')
    search_fields = ('name', 'location', 'industry', 'description')

    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'website', 'location', 'industry', 'description', 'logo')
        }),
        ('Additional Details', {
            'fields': ('founded_date', 'employee_count', 'revenue', 'categories', 'members', 'followers')
        }),
    )

    filter_horizontal = ('categories', 'members', 'followers')
    inlines = [AttachmentInline, CompanyUpdateInline]

@admin.register(CompanyUpdate)
class CompanyUpdateAdmin(admin.ModelAdmin):
    list_display = ('company', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('company__name', 'title')

    fieldsets = (
        ('Company Update Details', {
            'fields': ('company', 'title', 'content', 'created_at')
        }),
    )

    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        """Limit queryset to current user's Company Updates."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__members=request.user)

    def save_model(self, request, obj, form, change):
        """Override save_model to associate the current user with the Company Update."""
        if not obj.pk:
            obj.company = Company.objects.get(id=form.data.get('company'))
        obj.save()


