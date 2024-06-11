from django.db import models
from profiles.models import UserProfile

class SettingType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class UserSetting(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    setting_type = models.ForeignKey(SettingType, on_delete=models.CASCADE)
    value = models.TextField()

    class Meta:
        unique_together = ['user', 'setting_type']

    def __str__(self):
        return f"{self.user}'s {self.setting_type} setting"

    def save(self, *args, **kwargs):
        # Add custom validation logic before saving
        super(UserSetting, self).save(*args, **kwargs)

class GlobalSetting(models.Model):
    setting_type = models.ForeignKey(SettingType, on_delete=models.CASCADE)
    value = models.TextField()

    class Meta:
        unique_together = ['setting_type']

    def __str__(self):
        return str(self.setting_type)

    def save(self, *args, **kwargs):
        # Add custom validation logic before saving
        super(GlobalSetting, self).save(*args, **kwargs)