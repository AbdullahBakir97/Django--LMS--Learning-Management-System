from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Course, CourseEnrollment, CourseCompletion
from notifications.models import Notification

# Signal to send notification when a user enrolls in a course
@receiver(post_save, sender=CourseEnrollment)
def send_course_enrollment_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.student.userprofile
        course = instance.course
        notification_message = f"You have enrolled in the course '{course.title}'."
        Notification.objects.create(user=user, message=notification_message)

# Signal to send notification when a user completes a course
@receiver(post_save, sender=CourseCompletion)
def send_course_completion_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.student.userprofile
        course = instance.course
        notification_message = f"Congratulations! You have completed the course '{course.title}'."
        Notification.objects.create(user=user, message=notification_message)

# Signal to update completion count when a new course completion is added
@receiver(post_save, sender=CourseCompletion)
def update_completion_count(sender, instance, created, **kwargs):
    if created:
        course = instance.course
        course.completion_count = CourseCompletion.objects.filter(course=course).count()
        course.save()

# Signal to update enrollment count when a new course enrollment is added
@receiver(post_save, sender=CourseEnrollment)
def update_enrollment_count(sender, instance, created, **kwargs):
    if created:
        course = instance.course
        course.enrollment_count = CourseEnrollment.objects.filter(course=course).count()
        course.save()

# Signal to update enrollment count when a course enrollment is deleted
@receiver(post_delete, sender=CourseEnrollment)
def decrease_enrollment_count(sender, instance, **kwargs):
    course = instance.course
    course.enrollment_count = CourseEnrollment.objects.filter(course=course).count()
    course.save()

# Signal to update course duration when start or end time is changed
@receiver(post_save, sender=Course)
def update_course_duration(sender, instance, created, **kwargs):
    if not created:
        instance.duration_days = (instance.end_time - instance.start_time).days
        instance.save()

# Signal to delete associated course completions when a course is deleted
@receiver(post_delete, sender=Course)
def delete_associated_course_completions(sender, instance, **kwargs):
    CourseCompletion.objects.filter(course=instance).delete()

# Signal to delete associated course enrollments when a course is deleted
@receiver(post_delete, sender=Course)
def delete_associated_course_enrollments(sender, instance, **kwargs):
    CourseEnrollment.objects.filter(course=instance).delete()
