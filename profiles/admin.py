from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import User, UserProfile, Experience, Education, Skill, Endorsement, Achievement, Portfolio

# Inline class for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profiles'
    fk_name = 'user'

# Custom UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_picture_thumbnail', 'cover_photo_thumbnail')
    list_select_related = ('profile',)

    def profile_picture_thumbnail(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" style="width: 50px; height: 50px;"/>', obj.profile_picture.url)
        return None
    profile_picture_thumbnail.short_description = 'Profile Picture'

    def cover_photo_thumbnail(self, obj):
        if obj.cover_photo:
            return format_html('<img src="{}" style="width: 100px; height: 50px;"/>', obj.cover_photo.url)
        return None
    cover_photo_thumbnail.short_description = 'Cover Photo'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super(UserAdmin, self).get_inline_instances(request, obj)

# Register the UserAdmin
admin.site.register(User, UserAdmin)

# Admin registration for other models
class AchievementsInline(admin.TabularInline):
    model = Achievement
    extra = 1

class EndorsementsInline(admin.TabularInline):
    model = Endorsement
    fk_name = 'endorsed_user'
    extra = 1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = [AchievementsInline, EndorsementsInline]
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
    list_filter = ('user__user__username', 'company__name', 'start_date', 'end_date')
    search_fields = ('title', 'user__user__username', 'company__name')
    date_hierarchy = 'start_date'

    def user(self, obj):
        return obj.user_profile.user
    user.admin_order_field = 'user_profile__user'
    user.short_description = 'User'

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'user', 'institution', 'field_of_study', 'start_date', 'end_date')
    list_filter = ('user__user__username', 'institution', 'field_of_study', 'start_date', 'end_date')
    search_fields = ('degree', 'user__user__username', 'institution', 'field_of_study')
    date_hierarchy = 'start_date'

    def user(self, obj):
        return obj.user_profile.user
    user.admin_order_field = 'user_profile__user'
    user.short_description = 'User'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'proficiency', 'get_users_count')
    list_filter = ('proficiency',)
    search_fields = ('name',)
    filter_horizontal = ('users',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('users')

    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Users Count'

@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ('skill', 'endorsed_by', 'endorsed_user', 'created_at_display')
    list_filter = ('skill', 'endorsed_by', 'endorsed_user')
    search_fields = ('skill__name', 'endorsed_by__user__username', 'endorsed_user__user__username')
    filter_horizontal = ('shares',)
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        selected_ids = ','.join(str(obj.id) for obj in queryset)
        return HttpResponseRedirect(f'/admin/export/endorsements/?ids={selected_ids}')
    export_to_csv.short_description = 'Export selected endorsements to CSV'

    def created_at_display(self, obj):
        return obj.created_at
    created_at_display.short_description = 'Created At'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'date_achieved')
    list_filter = ('date_achieved',)
    search_fields = ('title', 'user__user__username')
    date_hierarchy = 'date_achieved'

    def user(self, obj):
        return obj.user_profile.user
    user.admin_order_field = 'user_profile__user'
    user.short_description = 'User'

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'user', 'project_url', 'created_at_display')
    search_fields = ('project_name', 'user__user__username')
    actions = ['mark_as_featured']

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} portfolio(s) marked as featured.')
    mark_as_featured.short_description = 'Mark selected as featured'

    def created_at_display(self, obj):
        return obj.created_at
    created_at_display.short_description = 'Created At'

    def user(self, obj):
        return obj.user_profile.user
    user.admin_order_field = 'user_profile__user'
    user.short_description = 'User'
