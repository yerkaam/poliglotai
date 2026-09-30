"""Email confirmation: a 6-digit code, valid 10 minutes, 5 attempts, resend after 60 seconds."""

import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import EmailCode

RESEND_SECONDS = 60


def _hash(user, code: str) -> str:
    return salted_hmac("poliglot.email-code", f"{user.pk}:{code}").hexdigest()


def send_code(user) -> None:
    EmailCode.objects.filter(user=user, used=False).update(used=True)  # only the newest code works
    code = settings.EMAIL_CODE_OVERRIDE or f"{secrets.randbelow(10**6):06d}"
    EmailCode.objects.create(
        user=user,
        code_hash=_hash(user, code),
        expires_at=timezone.now() + timedelta(minutes=settings.EMAIL_CODE_TTL_MINUTES),
    )
    send_mail(
        f"PoliglotAi — растау коды: {code}",
        f"Сәлем, {user.name}!\n\n"
        f"Поштаңызды растау коды: {code}\n\n"
        f"Код {settings.EMAIL_CODE_TTL_MINUTES} минут жарамды. "
        "Егер сіз PoliglotAi-да тіркелмесеңіз, бұл хатты елемеңіз.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


def check_code(user, code: str) -> str | None:
    """Marks the email verified and returns None, or returns the error message."""
    item = EmailCode.objects.filter(user=user, used=False).first()
    if item is None or item.expires_at < timezone.now():
        return "Кодтың мерзімі өтті. Жаңа код сұраңыз."
    if item.attempts >= settings.EMAIL_CODE_MAX_ATTEMPTS:
        return "Тым көп қате әрекет. Жаңа код сұраңыз."
    if not constant_time_compare(item.code_hash, _hash(user, code.strip())):
        item.attempts += 1
        item.save(update_fields=["attempts"])
        left = settings.EMAIL_CODE_MAX_ATTEMPTS - item.attempts
        return f"Код қате. Тағы {left} әрекет қалды." if left else "Тым көп қате әрекет. Жаңа код сұраңыз."
    item.used = True
    item.save(update_fields=["used"])
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    return None
