import tempfile

from .base import *  # noqa: F401

SECRET_KEY = "test-only-secret-key-long-enough-for-hs256-signing"  # noqa: S105
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
REST_AUTH = {**REST_AUTH, "JWT_AUTH_SECURE": False}
MEDIA_ROOT = tempfile.mkdtemp(prefix="lms-test-media-")
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {"anon": "10000/min", "user": "10000/min", "auth": "10000/min"},
}
