import logging
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)


class SMSConfigurationError(ValueError):
    pass


def _required_setting(name):
    value = getattr(settings, name, "")
    if value in (None, ""):
        raise SMSConfigurationError(f"{name} is not configured.")
    return value


def _gateway_mobile(phone_number):
    digits = "".join(ch for ch in str(phone_number or "") if ch.isdigit())
    country_code = "".join(ch for ch in str(getattr(settings, "SMS_MOBILE_COUNTRY_CODE", "") or "") if ch.isdigit())

    if country_code and len(digits) == 10:
        return f"{country_code}{digits}"
    return digits


def _is_gateway_failure(response_text):
    failure_markers = (
        "error",
        "fail",
        "invalid",
        "reject",
        "denied",
        "unauthor",
        "insufficient",
        "low balance",
        "no balance",
        "template mismatch",
        "invalid template",
    )
    return any(marker in response_text for marker in failure_markers)


def _is_gateway_success(response_text):
    success_markers = (
        "success",
        "sent",
        "submit",
        "accepted",
        "queued",
        "ok",
        "messageid",
        "msgid",
    )
    return any(marker in response_text for marker in success_markers)


def _safe_preview(body, limit=300):
    return " ".join((body or "").split())[:limit]


def send_phone_otp(phone_number, otp, user=None):
    """
    Send login OTP using the approved Hilite Multimedia SMS template.

    The gateway config is read from environment variables, so existing auth
    flows stay unchanged and production credentials are not hardcoded here.
    """
    if getattr(settings, "SKIP_SMS", False):
        logger.info(
            "Skipping phone OTP SMS because SKIP_SMS is enabled",
            extra={"phone_number": phone_number, "user_id": str(getattr(user, "id", ""))},
        )
        return

    api_url = _required_setting("SMS_API_URL")
    message_template = _required_setting("SMS_OTP_MESSAGE_TEMPLATE")
    message = message_template.format(otp=otp, user=user)

    params = {
        "username": _required_setting("SMS_USERNAME"),
        "apikey": _required_setting("SMS_API_KEY"),
        "apirequest": getattr(settings, "SMS_API_REQUEST", "Text"),
        "route": getattr(settings, "SMS_ROUTE", "ServiceImplicit"),
        "sender": _required_setting("SMS_SENDER_ID"),
        "mobile": _gateway_mobile(phone_number),
        "message": message,
        "TemplateID": _required_setting("SMS_TEMPLATE_ID"),
    }

    request_url = f"{api_url}?{urlencode(params)}"
    request = Request(request_url, method="GET")
    context = None
    if api_url.lower().startswith("https") and not getattr(settings, "SMS_VERIFY_SSL", True):
        context = ssl._create_unverified_context()

    try:
        with urlopen(request, timeout=15, context=context) as response:
            body = response.read().decode("utf-8", errors="replace")
            status_code = getattr(response, "status", 200)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "Phone OTP SMS gateway returned HTTP error",
            extra={"status_code": exc.code, "body": body[:500]},
        )
        raise ValueError("Failed to send OTP SMS.") from exc
    except URLError as exc:
        logger.error("Phone OTP SMS gateway request failed", extra={"reason": str(exc.reason)})
        raise ValueError("Failed to send OTP SMS.") from exc

    response_preview = _safe_preview(body)
    log_gateway_response = logger.warning if getattr(settings, "DEBUG", False) else logger.info
    log_gateway_response(
        "Phone OTP SMS gateway response received: status=%s mobile=%s response=%s",
        status_code,
        params["mobile"],
        response_preview,
        extra={
            "status_code": status_code,
            "phone_number": phone_number,
            "gateway_mobile": params["mobile"],
            "user_id": str(getattr(user, "id", "")),
            "response_preview": response_preview,
        },
    )

    response_text = body.lower()
    if status_code >= 400 or _is_gateway_failure(response_text):
        if getattr(settings, "DEBUG", False):
            raise ValueError(f"Failed to send OTP SMS: {response_preview}")
        raise ValueError("Failed to send OTP SMS.")

    if not _is_gateway_success(response_text):
        logger.warning(
            "Phone OTP SMS gateway returned an unrecognized success response",
            extra={
                "status_code": status_code,
                "phone_number": phone_number,
                "gateway_mobile": params["mobile"],
                "response_preview": response_preview,
            },
        )
