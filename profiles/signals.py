from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Skill, Experience, Education, Endorsement

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# Signal to manage endorsements
@receiver(post_save, sender=Endorsement)
def update_endorsement_count(sender, instance, created, **kwargs):
    if created:
        skill = instance.skill
        skill.endorsement_count += 1
        skill.save()

@receiver(post_delete, sender=Endorsement)
def decrease_endorsement_count(sender, instance, **kwargs):
    skill = instance.skill
    skill.endorsement_count -= 1
    skill.save()