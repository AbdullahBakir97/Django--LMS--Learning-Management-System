from django.db import models
from activity.models import Attachment
# from posts.models import Comment
# from certifications.models import Certification
from taggit.managers import TaggableManager
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachments = GenericRelation(Attachment)
    categories = models.ManyToManyField('activity.Category', related_name='courses_categories')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='instructed_courses', on_delete=models.CASCADE)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through='CourseEnrollment', related_name='enrolled_courses')
    shares = models.ManyToManyField('activity.Share', related_name='course_shares', blank=True)
    comments = models.ManyToManyField('posts.Comment', related_name='course_comments', blank=True)
    reactions = models.ManyToManyField('activity.Reaction', related_name='course_reactions', blank=True)
    tags = TaggableManager()

    def __str__(self):
        return self.title

class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, related_name='enrolled_courses', on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

class CourseCompletion(models.Model):
    course = models.ForeignKey(Course, related_name='completions', on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='completed_courses', on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    certificate_url = models.URLField()
    certificate = models.ForeignKey('certifications.Certification', related_name='course_completions', on_delete=models.SET_NULL, null=True, blank=True)
    tags = TaggableManager()

    def __str__(self):
        return f"{self.student.user.username} completed {self.course.title}"