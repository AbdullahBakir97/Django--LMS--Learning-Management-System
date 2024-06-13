from django.contrib import admin
from .models import UserProfile, Experience, Education, Skill, Endorsement, Achievement, Portfolio
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect

# Inline classes if necessary
class AchievementsInline(admin.TabularInline):
    model = Achievement
    extra = 1

class EndorsementsInline(admin.TabularInline):
    model = Endorsement
    extra = 1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = [
        AchievementsInline,
        EndorsementsInline,
    ]
    list_display = ('user', 'headline', 'location', 'joined_date', 'has_profile_picture', 'has_cover_photo')
    list_filter = ('location',)
    search_fields = ('user__username', 'headline', 'location')
    date_hierarchy = 'joined_date'
    actions = ['export_to_csv']

    def has_profile_picture(self, obj):
        return bool(obj.user.profile_picture)
    has_profile_picture.boolean = True
    has_profile_picture.short_description = 'Profile Picture'

    def has_cover_photo(self, obj):
        return bool(obj.user.cover_photo)
    has_cover_photo.boolean = True
    has_cover_photo.short_description = 'Cover Photo'

    def export_to_csv(self, request, queryset):
        selected_ids = ','.join(str(obj.user_id) for obj in queryset)
        return HttpResponseRedirect(f'/admin/export/userprofiles/?ids={selected_ids}')

    export_to_csv.short_description = 'Export selected profiles to CSV'

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'company', 'start_date', 'end_date')
    list_filter = ('user', 'company', 'start_date', 'end_date')
    search_fields = ('title', 'user__user__username', 'company__name')
    date_hierarchy = 'start_date'

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'user', 'institution', 'field_of_study', 'start_date', 'end_date')
    list_filter = ('user', 'institution', 'field_of_study', 'start_date', 'end_date')
    search_fields = ('degree', 'user__user__username', 'institution', 'field_of_study')
    date_hierarchy = 'start_date'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'proficiency', 'get_users_count')
    list_filter = ('proficiency',)
    search_fields = ('name',)
    filter_horizontal = ('users',)

    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Users Count'

@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ('skill', 'endorsed_by', 'endorsed_user', 'created_at')
    list_filter = ('skill', 'endorsed_by', 'endorsed_user')
    search_fields = ('skill__name', 'endorsed_by__user__username', 'endorsed_user__user__username')
    date_hierarchy = 'created_at'
    filter_horizontal = ('shares',)
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        selected_ids = ','.join(str(obj.id) for obj in queryset)
        return HttpResponseRedirect(f'/admin/export/endorsements/?ids={selected_ids}')

    export_to_csv.short_description = 'Export selected endorsements to CSV'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date_achieved')
    list_filter = ('date_achieved',)
    search_fields = ('title', 'user__user__username')
    date_hierarchy = 'date_achieved'

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'user', 'project_url', 'created_at')
    search_fields = ('project_name', 'user__user__username')
    date_hierarchy = 'created_at'
    actions = ['mark_as_featured']

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} portfolio(s) marked as featured.')

    mark_as_featured.short_description = 'Mark selected as featured'
