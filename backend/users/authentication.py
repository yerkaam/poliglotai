"""JWT stored in httpOnly cookies. The token is never readable from JavaScript."""

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
REMEMBER_COOKIE = "remember_me"


def _enforce_csrf(request):
    def dummy_get_response(_):
        return None

    check = CSRFCheck(dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw = request.COOKIES.get(ACCESS_COOKIE)
        if not raw:
            return None
        validated = self.get_validated_token(raw)
        _enforce_csrf(request)
        return self.get_user(validated), validated


def set_auth_cookies(response, access: str, refresh: str | None, remember: bool):
    common = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": "/",
    }
    access_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(ACCESS_COOKIE, access, max_age=access_age, **common)
    if refresh is not None:
        # AUTH-08: "remember me" keeps the session 30 days, otherwise until the browser closes.
        refresh_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()) if remember else None
        response.set_cookie(
            REFRESH_COOKIE,
            refresh,
            max_age=refresh_age,
            path="/api/auth/",
            **{k: v for k, v in common.items() if k != "path"},
        )
        response.set_cookie(
            REMEMBER_COOKIE,
            "1" if remember else "0",
            max_age=refresh_age,
            path="/api/auth/",
            **{k: v for k, v in common.items() if k != "path"},
        )


def clear_auth_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth/")
    response.delete_cookie(REMEMBER_COOKIE, path="/api/auth/")
