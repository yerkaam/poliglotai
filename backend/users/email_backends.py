"""Email over HTTPS, for hosts that block outgoing SMTP, such as Render's free plan.

- BrevoEmailBackend: Brevo's API (BREVO_API_KEY; DEFAULT_FROM_EMAIL must be a sender verified in Brevo).
- AppsScriptEmailBackend: a small Google Apps Script web app in the owner's own Google account sends the mail
  from their Gmail (deploy/gmail-sender.gs; GMAIL_SCRIPT_URL and GMAIL_SCRIPT_SECRET). No domain, no phone.
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


class AppsScriptEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages) -> int:
        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception("The Gmail script could not send an email")
        return sent

    def _send(self, message) -> None:
        name, _ = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        payload = {
            "secret": settings.GMAIL_SCRIPT_SECRET,
            "to": ",".join(parseaddr(to)[1] for to in message.to),
            "subject": message.subject,
            "body": message.body,
            "name": name or "PoliglotAi",
        }
        request = urllib.request.Request(
            settings.GMAIL_SCRIPT_URL,
            data=json.dumps(payload).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        # Google answers the POST with a redirect to the script's output; urllib follows it.
        with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            text = response.read().decode(errors="replace")
        try:
            result = json.loads(text)
        except ValueError:
            result = {}
        if not result.get("ok"):
            # e.g. a wrong secret, or the script deployed without "Anyone" access (Google's sign-in page comes back)
            raise RuntimeError(f"The Gmail script did not send the email: {result.get('error') or text[:200]}")
