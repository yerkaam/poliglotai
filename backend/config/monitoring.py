"""Error monitoring (Sentry). Off unless SENTRY_DSN is set; sends no personal data.

What leaves the server: the exception, its stack trace, the URL and the user's numeric id. Not sent:
request bodies (passwords, chat messages), cookies, headers with tokens, email addresses, IP addresses.
"""

import os

# Keys whose values never leave the server, wherever they appear in an event.
SECRET_KEYS = {"password", "password2", "old_password", "new_password", "code", "token", "refresh", "access", "text"}
REDACTED = "[Filtered]"


def _scrub(value):
    if isinstance(value, dict):
        return {k: REDACTED if str(k).lower() in SECRET_KEYS else _scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


def before_send(event, hint):
    request = event.get("request") or {}
    request.pop("data", None)
    request.pop("cookies", None)
    if request.get("query_string"):
        request["query_string"] = REDACTED  # the unsubscribe link carries a signed token
    headers = request.get("headers") or {}
    for name in list(headers):
        if name.lower() in {"cookie", "authorization", "x-csrftoken"}:
            headers[name] = REDACTED
    user = event.get("user")
    if user:
        event["user"] = {"id": user.get("id")} if user.get("id") else {}
    if "extra" in event:
        event["extra"] = _scrub(event["extra"])
    return event


def release() -> str:
    """The deployed commit: Render sets RENDER_GIT_COMMIT, other hosts can set SENTRY_RELEASE."""
    return os.environ.get("SENTRY_RELEASE") or os.environ.get("RENDER_GIT_COMMIT", "")[:12]


def init(dsn: str, environment: str) -> bool:
    if not dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release() or None,
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,  # locals can hold a learner's message or a password
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),
        before_send=before_send,
    )
    return True
