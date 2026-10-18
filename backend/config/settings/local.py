from .base import *  # noqa: F401

DEBUG = True
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
REST_AUTH = {**REST_AUTH, "JWT_AUTH_SECURE": False}
