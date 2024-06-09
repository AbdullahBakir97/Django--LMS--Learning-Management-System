# profiles/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from companies.models import Company

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    cover_photo = models.ImageField(upload_to='cover_photos/', blank=True)
    is_private = models.BooleanField(default=False)
    headline = models.CharField(max_length=255, blank=True)
    joined_date = models.DateTimeField(default=timezone.now)

    followers = models.ManyToManyField("self", related_name='following', symmetrical=False, blank=True)

    def __str__(self):
        return self.user.username

    def follow(self, profile):
        if not self.is_following(profile):
            self.following.add(profile)
            profile.followers.add(self)

    def unfollow(self, profile):
        if self.is_following(profile):
            self.following.remove(profile)
            profile.followers.remove(self)

    def is_following(self, profile):
        return self.following.filter(id=profile.id).exists()

class Experience(models.Model):
    user = models.ForeignKey(UserProfile, related_name='experiences', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='employees', on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
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

    def __str__(self):
        return self.name

class Endorsement(models.Model):
    skill = models.ForeignKey(Skill, related_name='endorsements', on_delete=models.CASCADE)
    endorsed_by = models.ForeignKey(UserProfile, related_name='given_endorsements', on_delete=models.CASCADE)
    endorsed_user = models.ForeignKey(UserProfile, related_name='received_endorsements', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.endorsed_by.user.username} endorsed {self.endorsed_user.user.username} for {self.skill.name}'
