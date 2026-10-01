"""The daily reminder email: "you have not studied today, your streak is waiting".

Sent once a day at the learner's hour, only to learners who studied within the last week (no mail to people
who left), never on a day they already studied. Every email has a one-click unsubscribe link.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.utils import timezone

from progress.models import ProgressLog
from progress.services import streak_days
from srs.models import UserVocabulary

from .models import Profile

logger = logging.getLogger(__name__)

ACTIVE_WITHIN_DAYS = 7
UNSUBSCRIBE_SALT = "poliglot.reminders.unsubscribe"


def unsubscribe_token(user) -> str:
    return signing.dumps(user.pk, salt=UNSUBSCRIBE_SALT)


def user_from_token(token: str):
    """The user id in a valid unsubscribe token, or None. The links do not expire: old emails keep working."""
    try:
        return signing.loads(token, salt=UNSUBSCRIBE_SALT)
    except signing.BadSignature:
        return None


def unsubscribe_url(user) -> str:
    # The site and the API share one address (single image, or nginx proxying /api).
    return f"{settings.FRONTEND_URL}/api/auth/reminders/unsubscribe/?token={unsubscribe_token(user)}"


def _studied(log: ProgressLog | None) -> bool:
    if log is None:
        return False
    return any(
        [log.reviews, log.new_words, log.trainer_total, log.chat_messages],
    )


def due_profiles(now=None):
    """Profiles that should get today's reminder at this hour."""
    now = timezone.localtime(now)
    today = now.date()
    recent = ProgressLog.objects.filter(date__gte=today - timedelta(days=ACTIVE_WITHIN_DAYS), date__lt=today)
    studied_today = {log.user_id for log in ProgressLog.objects.filter(date=today) if _studied(log)}
    candidates = (
        Profile.objects.filter(
            reminder_enabled=True,
            onboarded=True,
            reminder_hour__lte=now.hour,
            user__is_active=True,
            user__id__in=recent.values("user_id"),
        )
        .exclude(reminder_sent_on=today)
        .select_related("user")
    )
    if settings.REQUIRE_EMAIL_VERIFICATION:
        candidates = candidates.filter(user__email_verified=True)
    return [p for p in candidates if p.user_id not in studied_today]


def build_email(user) -> EmailMessage:
    today = timezone.localdate()
    streak = streak_days(user)
    due = UserVocabulary.objects.filter(
        user=user, status=UserVocabulary.Status.LEARNING, next_review_date__lte=today
    ).count()
    lines = [f"Сәлем, {user.name}!", ""]
    if streak:
        lines.append(f"Сіз {streak} күн қатарынан оқып келесіз. Бүгін де 10 минут бөлсеңіз, серия үзілмейді.")
    else:
        lines.append("Бүгін әлі сабақ болмады. 10 минут жеткілікті — бір қадам жасайық.")
    if due:
        lines.append(f"Қайталауды күтіп тұрған сөздер: {due}.")
    lines += [
        "",
        f"Сабақты жалғастыру: {settings.FRONTEND_URL}/words",
        "",
        "—",
        "Еске салғыштың уақытын «Баптаулар» бетінде өзгертуге болады.",
        f"Бұдан былай хат алмау: {unsubscribe_url(user)}",
    ]
    subject = f"PoliglotAi — {streak} күндік серияңызды сақтаңыз" if streak else "PoliglotAi — бүгінгі сабақ күтіп тұр"
    return EmailMessage(
        subject,
        "\n".join(lines),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        headers={
            "List-Unsubscribe": f"<{unsubscribe_url(user)}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )


def send_due(now=None) -> int:
    """Sends today's reminders that are due; returns how many went out. A failed email is retried next hour."""
    today = timezone.localdate(now)
    sent = 0
    for profile in due_profiles(now):
        try:
            build_email(profile.user).send()
        except Exception:
            logger.exception("Could not send the reminder to user %s", profile.user_id)
            continue
        profile.reminder_sent_on = today
        profile.save(update_fields=["reminder_sent_on"])
        sent += 1
    return sent
