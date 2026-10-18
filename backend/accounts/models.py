from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Defined now so no later migration has to swap the auth model."""

    email = models.EmailField("email address", unique=True)

    def __str__(self):
        return self.get_username()
