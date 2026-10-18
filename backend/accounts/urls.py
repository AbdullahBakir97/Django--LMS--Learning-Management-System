from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import (
    RegisterView,
    ResendEmailVerificationView,
    VerifyEmailView,
)
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import FrontendRedirectView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="rest_register"),
    path("verify-email/", VerifyEmailView.as_view(), name="rest_verify_email"),
    path("resend-email/", ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    path("login/", LoginView.as_view(), name="rest_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path("password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Links inside emails land here and are forwarded to the SPA.
    path(
        "confirm-email/<str:key>/",
        FrontendRedirectView.as_view(target="verify-email/{key}"),
        name="account_confirm_email",
    ),
    path(
        "reset-password/<str:uidb64>/<str:token>/",
        FrontendRedirectView.as_view(target="reset-password/{uidb64}/{token}"),
        name="password_reset_confirm",
    ),
]
