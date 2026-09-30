from django.conf import settings
from rest_framework.permissions import IsAuthenticated


class IsVerified(IsAuthenticated):
    """Logged in and the email confirmed with the code (when verification is on)."""

    message = "Алдымен поштаңызды растаңыз."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.email_verified or not settings.REQUIRE_EMAIL_VERIFICATION
