from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Email is the login id; username is the public handle used in URLs."""

    class Role(models.TextChoices):
        LEARNER = "learner", "Learner"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.LEARNER)

    def __str__(self):
        return self.get_username()

    def set_password(self, raw_password):
        """A new password (change or reset) signs out every device: their refresh tokens die."""
        super().set_password(raw_password)
        if self.pk:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            live = OutstandingToken.objects.filter(user=self, blacklistedtoken__isnull=True)
            BlacklistedToken.objects.bulk_create(
                [BlacklistedToken(token=t) for t in live], ignore_conflicts=True
            )

    @property
    def is_instructor(self) -> bool:
        return self.role in (self.Role.INSTRUCTOR, self.Role.ADMIN)
