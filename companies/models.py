from django.db import models
from activity.models import Attachment, Category
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    attachments = GenericRelation(Attachment)
    categories = models.ManyToManyField(Category, related_name='companies_categories')
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    founded_date = models.DateField(null=True, blank=True)
    employee_count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='member_companies')
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='followed_companies')

    def __str__(self):
        return self.name
    
    
class CompanyUpdate(models.Model):
    company = models.ForeignKey(Company, related_name='company_updates', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    attachments = GenericRelation(Attachment)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} Update: {self.title}"