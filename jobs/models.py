from django.db import models
from django.contrib.auth import get_user_model
# from profiles.models import Skill, Experience, Education, Endorsement  
from activity.models import Attachment
from django.contrib.contenttypes.fields import GenericRelation
from taggit.managers import TaggableManager
from django.conf import settings

class JobListing(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('education', 'Education'),
        ('contract', 'Contract'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry_level', 'Entry Level'),
        ('mid_level', 'Mid Level'),
        ('senior_level', 'Senior Level'),
    ]
    
    company = models.ForeignKey('companies.Company', related_name='job_listings_companies', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachments = GenericRelation('activity.Attachment')
    categories = models.ManyToManyField('activity.Category', related_name='job_listings_categories')
    location = models.CharField(max_length=255)
    posted_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    employment_type = models.CharField(
        max_length=50,
        choices=EMPLOYMENT_TYPES,
        blank=True
    )
    experience_level = models.CharField(
        max_length=50,
        choices=EXPERIENCE_LEVELS,
        blank=True
    )
    skills_required = models.ManyToManyField('profiles.Skill', related_name='required_jobs', blank=True, db_index=True)
    applications = models.ManyToManyField('JobApplication', related_name='applications_job_listings', blank=True, db_index=True)
    notifications = models.ManyToManyField('JobNotification', related_name='notifications_job_listings', blank=True, db_index=True)
    shares = models.ManyToManyField('activity.Share', related_name='shared_job_listings', blank=True)
    tags = TaggableManager()

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('interview', 'Interview'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
    ]
    job_listing = models.ForeignKey(JobListing, related_name='job_applications', on_delete=models.CASCADE, db_index=True)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='applications', on_delete=models.CASCADE, db_index=True)
    resume = models.FileField(upload_to='resumes/')
    attachments = GenericRelation('activity.Attachment')
    cover_letter = models.TextField(blank=True)
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied'
    )
    shares = models.ManyToManyField('activity.Share', related_name='shared_applications', blank=True)

    def __str__(self):
        return f'{self.applicant.username} applied for {self.job_listing.title}'
    
class JobNotification(models.Model):
    job_listing = models.ForeignKey(JobListing, related_name='job_notifications', on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    shares = models.ManyToManyField('activity.Share', related_name='shared_notifications', blank=True)

    def __str__(self):
        return f'{self.user.username} received a notification for {self.job_listing.title}'