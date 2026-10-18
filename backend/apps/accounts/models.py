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

    @property
    def is_instructor(self) -> bool:
        return self.role in (self.Role.INSTRUCTOR, self.Role.ADMIN)
