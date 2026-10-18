from django.conf import settings
from django.http import HttpResponseRedirect
from django.views import View


class FrontendRedirectView(View):
    """allauth and dj-rest-auth put these URL names in emails; the SPA finishes the flow."""

    target = ""

    def get(self, request, **kwargs):
        path = self.target.format(**kwargs)
        return HttpResponseRedirect(f"{settings.FRONTEND_URL.rstrip('/')}/{path}")
