"""Email over an HTTPS API (Brevo), for hosts that block outgoing SMTP, such as Render's free plan.

Set BREVO_API_KEY and the app sends through it; DEFAULT_FROM_EMAIL must be a sender verified in Brevo.
No extra dependency: one JSON POST per message with the standard library.
"""

import json
import logging
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages) -> int:
        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception("Brevo could not send an email")
        return sent

    def _send(self, message) -> None:
        name, address = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        payload = {
            "sender": {"name": name or "PoliglotAi", "email": address},
            "to": [{"email": parseaddr(to)[1]} for to in message.to],
            "subject": message.subject,
            "textContent": message.body,
        }
        if message.extra_headers:
            payload["headers"] = dict(message.extra_headers)
        request = urllib.request.Request(
            BREVO_URL,
            data=json.dumps(payload).encode(),
            headers={
                "api-key": settings.BREVO_API_KEY,
                "content-type": "application/json",
                "accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            # Brevo explains the problem (unverified sender, bad key) in the body: keep it for the logs.
            detail = exc.read().decode(errors="replace")[:500]
            raise RuntimeError(f"Brevo answered {exc.code}: {detail}") from exc
