import json
import re
import urllib.error
import urllib.request

from django.conf import settings


class DoubleTickProviderError(Exception):
    retryable = False

    def __init__(self, message, provider_payload=None):
        super().__init__(message)
        self.provider_payload = provider_payload or {}


class DoubleTickTransientError(DoubleTickProviderError):
    retryable = True


class DoubleTickPermanentError(DoubleTickProviderError):
    retryable = False


def digits_only(value):
    return re.sub(r"\D", "", str(value or ""))


def template_endpoint():
    base_url = getattr(settings, "DOUBLETICK_BASE_URL", "https://public.doubletick.io").rstrip("/")
    endpoint = getattr(settings, "DOUBLETICK_SEND_TEMPLATE_ENDPOINT", "/whatsapp/message/template")
    return endpoint if str(endpoint).startswith(("http://", "https://")) else f"{base_url}/{str(endpoint).lstrip('/')}"


class DoubleTickTemplateProvider:
    """Production adapter for the confirmed DoubleTick template-message API."""

    TEMPLATE_NAME = "night_spa_recommendation"
    LANGUAGE = "en"

    @classmethod
    def build_payload(cls, to, from_waba, variables):
        recipient = digits_only(to)
        sender = digits_only(from_waba)
        if not recipient or len(recipient) < 10:
            raise DoubleTickPermanentError("INVALID_RECIPIENT")
        if not sender:
            raise DoubleTickPermanentError("DOUBLETICK_WABA_SENDER_NOT_CONFIGURED")
        if len(variables) != 3 or any(value in (None, "") for value in variables):
            raise DoubleTickPermanentError("INVALID_TEMPLATE_VARIABLES")
        return {
            "messages": [
                {
                    "to": recipient,
                    "from": sender,
                    "content": {
                        "templateName": cls.TEMPLATE_NAME,
                        "language": cls.LANGUAGE,
                        "templateData": {
                            "body": {
                                "placeholders": list(variables),
                            }
                        },
                    },
                }
            ]
        }

    @staticmethod
    def _safe_error_payload(status_code=None, body=""):
        payload = {"status_code": status_code}
        if body:
            payload["body"] = body[:1000]
        return payload

    @classmethod
    def send(cls, to, from_waba, variables):
        api_key = getattr(settings, "DOUBLETICK_API_KEY", "")
        if not api_key:
            raise DoubleTickPermanentError("DOUBLETICK_API_KEY_NOT_CONFIGURED")

        payload = cls.build_payload(to, from_waba, variables)
        request = urllib.request.Request(
            template_endpoint(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Authorization": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body or "{}")
                status_code = response.status
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""
            safe_payload = cls._safe_error_payload(exc.code, body)
            if 500 <= exc.code <= 599:
                raise DoubleTickTransientError(f"DOUBLETICK_HTTP_{exc.code}", safe_payload) from exc
            raise DoubleTickPermanentError(f"DOUBLETICK_HTTP_{exc.code}", safe_payload) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise DoubleTickTransientError("DOUBLETICK_TRANSIENT_SEND_FAILURE", {"error": str(exc)}) from exc
        except ValueError as exc:
            raise DoubleTickPermanentError("DOUBLETICK_MALFORMED_RESPONSE") from exc

        message_id = parsed.get("messageId")
        if not message_id:
            raise DoubleTickPermanentError("DOUBLETICK_MESSAGE_ID_MISSING", parsed)
        return {
            "message_id": str(message_id),
            "provider_payload": {"status_code": status_code, "body": parsed},
            "request_payload": payload,
        }
