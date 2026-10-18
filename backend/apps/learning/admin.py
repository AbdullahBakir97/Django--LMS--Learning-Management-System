from django.contrib import admin

from .models import Certificate, Choice, Course, Enrollment, Lesson, Question, Quiz


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("order", "title", "is_free_preview")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "status", "level", "published_at")
    list_filter = ("status", "level")
    search_fields = ("title", "instructor__username")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "order")
    inlines = [ChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "pass_score")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "completed_at")
    list_filter = ("status",)


admin.site.register(Certificate)
