import re
from html import escape
from urllib.parse import urlparse

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


FORM_KEY_RE = re.compile(r"^frm_[a-z0-9_]{4,70}$")


def sanitize_text(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return escape(value, quote=False)


def normalize_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[-10:]
    if len(digits) < 10 or len(digits) > 15:
        raise serializers.ValidationError("Enter a valid phone number.")
    return digits


def validate_required_text(value, field_name):
    cleaned = sanitize_text(value)
    if not cleaned:
        raise serializers.ValidationError(f"{field_name} is required.")
    return cleaned


def validate_short_text(value, field_name, max_length=20, required=False):
    cleaned = sanitize_text(value)
    if required and not cleaned:
        raise serializers.ValidationError(f"{field_name} is required.")
    if len(cleaned) > max_length:
        raise serializers.ValidationError(f"{field_name} must be {max_length} characters or fewer.")
    return cleaned


def validate_form_key(value):
    cleaned = sanitize_text(value).lower()
    if not cleaned:
        raise serializers.ValidationError("form_key is required.")
    if not FORM_KEY_RE.match(cleaned):
        raise serializers.ValidationError("Invalid form key.")
    return cleaned


def validate_url(value, required=False):
    cleaned = str(value or "").strip()
    if required and not cleaned:
        raise serializers.ValidationError("URL is required.")
    if not cleaned:
        return ""
    try:
        URLValidator()(cleaned)
    except DjangoValidationError:
        raise serializers.ValidationError("Enter a valid URL.")
    return cleaned


def same_domain_or_subdomain(url, allowed_url):
    if not url or not allowed_url:
        return True
    source = urlparse(url).hostname or ""
    allowed = urlparse(allowed_url).hostname or ""
    return source == allowed or source.endswith(f".{allowed}")
