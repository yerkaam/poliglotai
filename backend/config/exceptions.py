"""Every API error is JSON in one shape: {"detail": "...", "code": "..."} plus field errors if any.

Without this, an unexpected exception or an unknown /api/ address returns Django's HTML page and the
frontend can only guess what happened.
"""

import logging

import sentry_sdk
from django.http import JsonResponse
from rest_framework.views import exception_handler

logger = logging.getLogger("poliglot.errors")

SERVER_ERROR = "Серверде қате болды. Бірнеше минуттан кейін қайталап көріңіз."
NOT_FOUND = "Мұндай бет немесе дерек жоқ."
CODE_BY_STATUS = {
    400: "invalid",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    429: "throttled",
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        # Not an API exception: a bug. Log it with the request and answer in the usual JSON shape.
        request = context.get("request")
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            sentry_sdk.set_user({"id": user.pk})  # the id only, to find the account; no email
        logger.exception("Unhandled API error on %s %s", getattr(request, "method", "?"), getattr(request, "path", "?"))
        return JsonResponse({"detail": SERVER_ERROR, "code": "server_error"}, status=500)

    data = response.data
    if isinstance(data, list):
        data = {"detail": " ".join(str(item) for item in data)}
    elif isinstance(data, dict) and "detail" not in data and "non_field_errors" in data:
        data = {**data, "detail": " ".join(str(e) for e in data["non_field_errors"])}
    if isinstance(data, dict):
        if response.status_code == 404:
            data["detail"] = NOT_FOUND  # Django's own text is English ("No Vocabulary matches…")
        code = getattr(exc, "default_code", None) if "detail" in data else None
        data.setdefault("code", code or CODE_BY_STATUS.get(response.status_code, "error"))
    response.data = data
    return response


def json_404(request, exception=None):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": NOT_FOUND, "code": "not_found"}, status=404)
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)


def json_500(request):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": SERVER_ERROR, "code": "server_error"}, status=500)
    from django.views.defaults import server_error

    return server_error(request)
