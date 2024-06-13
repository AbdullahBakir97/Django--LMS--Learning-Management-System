from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
# from jobs.models import JobApplication, JobListing
from followers.models import Follower, FollowRequest, FollowNotification
# from notifications.models import Notification
from shortuuidfield import ShortUUIDField
# from messaging.models import Reaction, Share

class User(AbstractUser):
    userId = ShortUUIDField()
    profile_picture = models.ImageField(upload_to="users_images/", null=True, blank=True)
    cover_photo = models.ImageField(upload_to="cover_photos/", null=True, blank=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', db_index=True)
    bio = models.TextField(blank=True)
    headline = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_private = models.BooleanField(default=False)
    joined_date = models.DateTimeField(default=timezone.now)
    followers = models.ManyToManyField("self", through='Follower', related_name='following', symmetrical=False, db_index=True)
    skills = models.ManyToManyField('Skill', related_name='users_skills', blank=True, db_index=True)
    experiences = models.ManyToManyField('Experience', related_name='users_experiences', blank=True, db_index=True)
    educations = models.ManyToManyField('Education', related_name='users_educations', blank=True, db_index=True)
    endorsements = models.ManyToManyField('Endorsement', related_name='users_endorsements', blank=True, db_index=True)
    job_applications = models.ManyToManyField('jobs.JobApplication', related_name='profile_job_applications', blank=True)
    job_listings = models.ManyToManyField('jobs.JobListing', related_name='profile_job_listings', blank=True)
    notifications = models.ManyToManyField('notifications.Notification', related_name='profile_notifications', blank=True)
    followers = models.ManyToManyField(Follower, related_name='users_followers', blank=True)
    follow_requests = models.ManyToManyField(FollowRequest, related_name='users_follow_requests', blank=True)
    shares = models.ManyToManyField('activity.Share', related_name='users_shares', blank=True)
    
    
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
            
    def endorse_skill(self, skill, endorsed_by):
        if not self.has_endorsed(skill):
            Endorsement.objects.create(skill=skill, endorsed_by=endorsed_by, endorsed_user=self)

    def has_endorsed(self, skill):
        return Endorsement.objects.filter(skill=skill, endorsed_user=self).exists()

    def add_experience(self, title, company, description, start_date, end_date=None, is_current=False):
        return Experience.objects.create(
            user_profile=self,
            title=title,
            company=company,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current
        )

    def add_education(self, institution, degree, field_of_study, start_date, end_date=None, is_current=False):
        return Education.objects.create(
            user_profile=self,
            institution=institution,
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current
        )

class Experience(models.Model):
    user = models.ForeignKey(UserProfile, related_name='user_experiences', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    company = models.ForeignKey('companies.Company', related_name='employees', on_delete=models.SET_NULL, null=True, db_index=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    shares = models.ManyToManyField('activity.Share', related_name='experience_shares', blank=True)

    def __str__(self):
        return f'{self.title} at {self.company.name if self.company else "N/A"}'

class Education(models.Model):
    user = models.ForeignKey(UserProfile, related_name='user_educations', on_delete=models.CASCADE, db_index=True)
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    shares = models.ManyToManyField('activity.Share', related_name='education_shares', blank=True)

    def __str__(self):
        return f'{self.degree} in {self.field_of_study} from {self.institution}'

class Skill(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(UserProfile, related_name='user_skills', db_index=True)
    proficiency = models.CharField(max_length=50)
    shares = models.ManyToManyField('activity.Share', related_name='skill_shares', blank=True)
    endorsements = models.ManyToManyField('Endorsement', related_name='endorsement_skills', blank=True, db_index=True)
    job_applications = models.ManyToManyField('jobs.JobApplication', related_name='skill_job_applications', blank=True)
    job_listings = models.ManyToManyField('jobs.JobListing', related_name='skill_job_listings', blank=True)
    notifications = models.ManyToManyField('notifications.Notification', related_name='skill_notifications', blank=True)
    verified_from = models.ManyToManyField(UserProfile, related_name='skill_verified_from', blank=True)
    verified_to = models.ManyToManyField(UserProfile, related_name='skill_verified_to', blank=True)

    def __str__(self):
        return self.name

class Endorsement(models.Model):
    skill = models.ForeignKey(Skill, related_name='skills_endorsements', on_delete=models.CASCADE, db_index=True)
    endorsed_by = models.ForeignKey(UserProfile, related_name='given_endorsements', on_delete=models.CASCADE, db_index=True)
    endorsed_user = models.ForeignKey(UserProfile, related_name='received_endorsements', on_delete=models.CASCADE, db_index=True)
    shares = models.ManyToManyField('activity.Share', related_name='endorsement_shares', blank=True)

    def __str__(self):
        return f'{self.endorsed_by.user.username} endorsed {self.endorsed_user.user.username} for {self.skill.name}'
    
class Achievement(models.Model):
    user = models.ForeignKey(UserProfile, related_name='achievements', on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_achieved = models.DateField()

    def __str__(self):
        return self.title
    
class Portfolio(models.Model):
    user = models.ForeignKey(UserProfile, related_name='portfolio', on_delete=models.CASCADE, db_index=True)
    project_name = models.CharField(max_length=255)
    description = models.TextField()
    project_url = models.URLField()

    def __str__(self):
        return self.project_name