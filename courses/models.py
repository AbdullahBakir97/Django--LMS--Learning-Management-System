from django.db import models
from profiles.models import UserProfile
from activity.models import Attachment, Reaction, Share, Tag, Category
from posts.models import Comment
from certifications.models import Certification
from django.contrib.contenttypes.fields import GenericRelation

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachments = GenericRelation(Attachment)
    categories = models.ManyToManyField(Category, related_name='courses_categories')
    instructor = models.ForeignKey(UserProfile, related_name='instructed_courses', on_delete=models.CASCADE)
    students = models.ManyToManyField(UserProfile, through='CourseEnrollment', related_name='enrolled_courses')
    shares = models.ManyToManyField(Share, related_name='course_shares', blank=True)
    comments = models.ManyToManyField(Comment, related_name='course_comments', blank=True)
    reactions = models.ManyToManyField(Reaction, related_name='course_reactions', blank=True)
    tags = models.ManyToManyField(Tag, related_name='tagged_courses', blank=True)

    def __str__(self):
        return self.title

class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    student = models.ForeignKey(UserProfile, related_name='enrolled_courses', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

class CourseCompletion(models.Model):
    course = models.ForeignKey(Course, related_name='completions', on_delete=models.CASCADE)
    student = models.ForeignKey(UserProfile, related_name='completed_courses', on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    certificate_url = models.URLField()
    certificate = models.ForeignKey(Certification, 'course_completions', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='tagged_courses_completion', blank=True)

    def __str__(self):
        return f"{self.student.user.username} completed {self.course.title}"