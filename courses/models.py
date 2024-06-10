from django.db import models
from profiles.models import UserProfile
from messaging.models import Reaction, Share, Tag
from posts.models import Comment
from certifications.models import Certification

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(UserProfile, related_name='instructed_courses', on_delete=models.CASCADE)
    students = models.ManyToManyField(UserProfile, through='CourseEnrollment', related_name='enrolled_courses')
    shares = models.ManyToManyField(Share, related_name='course_shares', blank=True)
    comments = models.ManyToManyField(Comment, related_name='course_comments', blank=True)
    reactions = models.ManyToManyField(Reaction, related_name='course_reactions', blank=True)
    tags = models.ManyToManyField(Tag, related_name='tagged_courses', blank=True)

    def __str__(self):
        return self.title

class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

class CourseCompletion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    certificate_url = models.URLField()
    certificate = models.ForeignKey(Certification, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='tagged_courses_completion', blank=True)

    def __str__(self):
        return f"{self.student.user.username} completed {self.course.title}"