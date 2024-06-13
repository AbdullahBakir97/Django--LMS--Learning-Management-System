from django.db import models
from django.conf import settings
from activity.models import Attachment
from django.contrib.contenttypes.fields import GenericRelation

class Certification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_certifications', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    attachments = GenericRelation(Attachment)
    issuing_organization = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=255, blank=True)
    credential_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField('activity.Category', related_name='certifications_categories')
    certificate_image = models.ImageField(upload_to='certificates/', blank=True)
    verification_status = models.BooleanField(default=False)
    related_jobs = models.ManyToManyField('jobs.JobListing', related_name='job_certifications', blank=True)
    related_courses = models.ManyToManyField('courses.Course', related_name='courses_certifications', blank=True)

    def __str__(self):
        return f"{self.name} - {self.user.user.username}"
