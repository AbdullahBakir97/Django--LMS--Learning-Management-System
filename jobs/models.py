from django.db import models
from companies.models import Company
from profiles.models import UserProfile, Skill, Experience, Education, Endorsement  

class JobListing(models.Model):
    company = models.ForeignKey(Company, related_name='job_listings', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    posted_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    employment_type = models.CharField(max_length=50,choices=[('full_time', 'Full Time'), ('part_time', 'Part Time'), ('education', 'Education'), ('contract', 'Contract')], blank=True)
    experience_level = models.CharField(max_length=50,choices=[('entry_level', 'Entry Level'), ('mid_level', 'Mid Level'), ('senior_level', 'Senior Level')], blank=True)
    skills_required = models.ManyToManyField(Skill, related_name='jobs', blank=True)

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    job_listing = models.ForeignKey(JobListing, related_name='applications', on_delete=models.CASCADE)
    applicant = models.ForeignKey(UserProfile, related_name='job_applications', on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('applied', 'Applied'), ('reviewed', 'Reviewed'), ('interview', 'Interview'), ('offered', 'Offered'), ('rejected', 'Rejected')], default='applied')

    def __str__(self):
        return f'{self.applicant.user.username} applied for {self.job_listing.title}'
    
    
class JobNotification(models.Model):
    job_listing = models.ForeignKey(JobListing, related_name='notifications', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, related_name='job_notifications', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.user.username} received a notification for {self.job_listing.title}'