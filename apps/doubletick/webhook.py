from django.conf import settings


def get_webhook_secret_from_request(request):
    """Read DoubleTick secret from either the provider header or query string."""
    return request.headers.get("X-DoubleTick-Secret") or request.query_params.get("secret")


def is_valid_doubletick_webhook(request):
    """
    Verify DoubleTick webhook requests without JWT.

    Provider webhooks are server-to-server calls, so they use a shared secret
    configured in DOUBLETICK_WEBHOOK_SECRET.
    """
    expected_secret = getattr(settings, "DOUBLETICK_WEBHOOK_SECRET", "")
    received_secret = get_webhook_secret_from_request(request)
    return bool(expected_secret and received_secret == expected_secret)
