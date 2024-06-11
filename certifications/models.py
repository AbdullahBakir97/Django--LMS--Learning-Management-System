from django.db import models
from profiles.models import UserProfile
from jobs.models import JobListing
from courses.models import Course
from activity.models import Attachment, Category
from django.contrib.contenttypes.fields import GenericRelation

class Certification(models.Model):
    user = models.ForeignKey(UserProfile, related_name='user_certifications', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    attachments = GenericRelation(Attachment)
    issuing_organization = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=255, blank=True)
    credential_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name='certifications_categories')
    certificate_image = models.ImageField(upload_to='certificates/', blank=True)
    verification_status = models.BooleanField(default=False)
    related_jobs = models.ManyToManyField(JobListing, related_name='job_certifications', blank=True)
    related_courses = models.ManyToManyField(Course, related_name='courses_certifications', blank=True)

    def __str__(self):
        return f"{self.name} - {self.user.user.username}"
