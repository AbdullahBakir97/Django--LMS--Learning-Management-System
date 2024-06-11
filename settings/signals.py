from django.db.models.signals import post_save
from django.dispatch import receiver
from profiles.models import UserProfile
from .models import UserSetting, GlobalSetting, SettingType

@receiver(post_save, sender=UserProfile)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        # Create default user settings for a new user
        default_setting_type = SettingType.objects.get_or_create(name='default_user_setting', description='Default User Setting')[0]
        UserSetting.objects.create(user=instance, setting_type=default_setting_type, value='default_value')

@receiver(post_save, sender=SettingType)
def create_global_settings(sender, instance, created, **kwargs):
    if created:
        # Create global settings based on new setting types
        GlobalSetting.objects.get_or_create(setting_type=instance, value='default_value')