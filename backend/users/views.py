from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import REFRESH_COOKIE, REMEMBER_COOKIE, clear_auth_cookies, set_auth_cookies
from .models import Profile, User
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)

LOGIN_ERROR = "Пошта немесе құпиясөз қате"
RESET_SENT = "Егер бұл пошта тіркелген болса, 5 минут ішінде сілтеме келеді."
RESEND_SECONDS = 60


def _login_response(user, remember: bool, status_code=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    response = Response(UserSerializer(user).data, status=status_code)
    set_auth_cookies(response, str(refresh.access_token), str(refresh), remember)
    return response


def _client_ip(request):
    return request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """Sets the csrftoken cookie that Angular echoes back in X-CSRFToken."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"ok": True})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _login_response(user, remember=True, status_code=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": LOGIN_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"].lower().strip()

        # AUTH-09: 5 failed logins within 15 minutes lock the email (and IP) for 15 minutes.
        keys = [f"login-fail:email:{email}", f"login-fail:ip:{_client_ip(request)}"]
        if any((cache.get(k) or 0) >= settings.LOGIN_MAX_FAILURES for k in keys):
            return Response(
                {"detail": "Тым көп сәтсіз әрекет. 15 минуттан кейін қайталаңыз.", "code": "locked"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(request, email=email, password=serializer.validated_data["password"])
        if user is None:
            for key in keys:
                if not cache.add(key, 1, settings.LOGIN_LOCKOUT_SECONDS):
                    try:
                        cache.incr(key)
                    except ValueError:
                        cache.set(key, 1, settings.LOGIN_LOCKOUT_SECONDS)
            # AUTH-06: one generic message, never which field was wrong.
            return Response({"detail": LOGIN_ERROR}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete_many(keys)
        return _login_response(user, remember=serializer.validated_data["remember"])


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.COOKIES.get(REFRESH_COOKIE)
        if not raw:
            return Response({"detail": "No session"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            old = RefreshToken(raw)
            user = User.objects.get(pk=old["user_id"], is_active=True)
            old.blacklist()
        except (TokenError, User.DoesNotExist):
            response = Response({"detail": "Session expired"}, status=status.HTTP_401_UNAUTHORIZED)
            clear_auth_cookies(response)
            return response
        new = RefreshToken.for_user(user)
        response = Response({"ok": True})
        remember = request.COOKIES.get(REMEMBER_COOKIE) == "1"
        set_auth_cookies(response, str(new.access_token), str(new), remember)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.COOKIES.get(REFRESH_COOKIE)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProfileView(APIView):
    """AUTH-04: after registration the learner sets level and daily goal."""

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        # AUTH-12: resend no sooner than 60 s. Applies to every email so it reveals nothing.
        if not cache.add(f"reset-sent:{email}", 1, RESEND_SECONDS):
            return Response(
                {"detail": "Хатты 60 секундтан кейін қайта жіберуге болады.", "retry_after": RESEND_SECONDS},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset/confirm?uid={uid}&token={token}"
            send_mail(
                "PoliglotAi — құпиясөзді қалпына келтіру",
                f"Сәлем, {user.name}!\n\nЖаңа құпиясөз орнату үшін сілтемені ашыңыз (1 сағат жарамды):\n{link}\n\n"
                "Егер сіз сұрамасаңыз, бұл хатты елемеңіз.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        # AUTH-11: identical answer for registered and unknown emails.
        return Response({"detail": RESET_SENT, "retry_after": RESEND_SECONDS})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data["uid"])))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        # The token hashes the password and timestamp: valid for 1 hour and only once.
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "Сілтеме жарамсыз немесе мерзімі өтіп кеткен. Жаңасын сұраңыз."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(data["password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Құпиясөз жаңартылды. Енді кіре аласыз."})
