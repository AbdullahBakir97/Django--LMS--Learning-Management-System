from django.contrib import admin

from .models import (
    Achievement,
    Education,
    Endorsement,
    Experience,
    PortfolioItem,
    Profile,
    ProfileSkill,
    Skill,
)


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 0


class ProfileSkillInline(admin.TabularInline):
    model = ProfileSkill
    extra = 0
    autocomplete_fields = ["skill"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "location", "updated_at")
    search_fields = ("user__username", "user__email", "headline")
    inlines = [ExperienceInline, EducationInline, PortfolioItemInline, ProfileSkillInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


admin.site.register(Endorsement)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at")
    list_filter = ("code",)
    search_fields = ("user__username",)
