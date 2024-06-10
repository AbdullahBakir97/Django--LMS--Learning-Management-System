from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from companies.models import CompanyUpdate
from jobs.models import JobApplication, JobListing
from followers.models import Follower, FollowRequest, FollowNotification
from notifications.models import Notification
from shortuuidfield import ShortUUIDField

class User(AbstractUser):
    userId = ShortUUIDField()
    profile_picture = models.ImageField(upload_to="users_images/", null=True, blank=True)
    cover_photo = models.ImageField(upload_to="cover_photos/", null=True, blank=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    headline = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_private = models.BooleanField(default=False)
    joined_date = models.DateTimeField(default=timezone.now)
    followers = models.ManyToManyField("self", through='Follower', related_name='following', symmetrical=False)
    skills = models.ManyToManyField('Skill', related_name='users_skills', blank=True)
    experiences = models.ManyToManyField('Experience', related_name='users_experiences', blank=True)
    educations = models.ManyToManyField('Education', related_name='users_educations', blank=True)
    endorsements = models.ManyToManyField('Endorsement', related_name='users_endorsements', blank=True)
    job_applications = models.ManyToManyField(JobApplication, related_name='users_job_applications', blank=True)
    job_listings = models.ManyToManyField(JobListing, related_name='users_job_listings', blank=True)
    notifications = models.ManyToManyField(Notification, related_name='users_notifications', blank=True)
    followers = models.ManyToManyField(Follower, related_name='users_followers', blank=True)
    follow_requests = models.ManyToManyField(FollowRequest, related_name='users_follow_requests', blank=True)
    
    
    def __str__(self):
        return self.user.username

    def follow(self, profile):
        if not self.is_following(profile):
            if profile.is_private:
                FollowRequest.objects.create(from_user=self, to_user=profile)
            else:
                Follower.objects.create(user=profile, follower=self)

    def unfollow(self, profile):
        Follower.objects.filter(user=profile, follower=self).delete()

    def is_following(self, profile):
        return Follower.objects.filter(user=profile, follower=self).exists()

    def has_follow_request(self, profile):
        return FollowRequest.objects.filter(from_user=self, to_user=profile).exists()

    def accept_follow_request(self, profile):
        follow_request = FollowRequest.objects.filter(from_user=profile, to_user=self).first()
        if follow_request:
            follow_request.accept()

    def reject_follow_request(self, profile):
        follow_request = FollowRequest.objects.filter(from_user=profile, to_user=self).first()
        if follow_request:
            follow_request.reject()

class Experience(models.Model):
    user = models.ForeignKey(UserProfile, related_name='experiences', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    company = models.ForeignKey('companies.Company', related_name='employees', on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title} at {self.company.name if self.company else "N/A"}'

class Education(models.Model):
    user = models.ForeignKey(UserProfile, related_name='educations', on_delete=models.CASCADE)
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.degree} in {self.field_of_study} from {self.institution}'

class Skill(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(UserProfile, related_name='skills')
    proficiency = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Endorsement(models.Model):
    skill = models.ForeignKey(Skill, related_name='endorsements', on_delete=models.CASCADE)
    endorsed_by = models.ForeignKey(UserProfile, related_name='given_endorsements', on_delete=models.CASCADE)
    endorsed_user = models.ForeignKey(UserProfile, related_name='received_endorsements', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.endorsed_by.user.username} endorsed {self.endorsed_user.user.username} for {self.skill.name}'