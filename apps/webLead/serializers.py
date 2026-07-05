from rest_framework import serializers

from apps.branches.models import Branch
from apps.accounts.models.user import User

from .models import (
    WebsiteFormConfiguration,
    WebsiteLead,
    WebsiteLeadActivity,
    WebsiteLeadStatus,
)
from .services import generate_form_key
from .validators import (
    normalize_phone,
    sanitize_text,
    validate_form_key,
    validate_required_text,
    validate_short_text,
    validate_url,
)


class WebsiteFormConfigurationSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = WebsiteFormConfiguration
        fields = [
            "id",
            "branch",
            "branch_name",
            "website_name",
            "website_url",
            "form_key",
            "form_title",
            "primary_color",
            "background_color",
            "button_color",
            "text_color",
            "border_radius",
            "font_family",
            "theme",
            "submit_button_text",
            "success_message",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
        extra_kwargs = {"form_key": {"required": False, "allow_blank": True}}

    def validate_website_name(self, value):
        return validate_required_text(value, "website_name")

    def validate_website_url(self, value):
        return validate_url(value, required=True)

    def validate_form_key(self, value):
        if not value:
            return value
        value = validate_form_key(value)
        qs = WebsiteFormConfiguration.objects.filter(form_key=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This form key is already in use.")
        return value

    def validate(self, attrs):
        if not attrs.get("form_key") and not self.instance:
            attrs["form_key"] = generate_form_key(attrs.get("website_name"))
        return attrs


class PublicWebsiteFormConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteFormConfiguration
        fields = [
            "form_key",
            "form_title",
            "website_name",
            "primary_color",
            "background_color",
            "button_color",
            "text_color",
            "border_radius",
            "font_family",
            "theme",
            "submit_button_text",
            "success_message",
            "is_active",
        ]


class WebsiteLeadSubmitSerializer(serializers.Serializer):
    form_key = serializers.CharField()
    name = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField(max_length=20)
    notes = serializers.CharField(max_length=20, required=False, allow_blank=True)
    submitted_from_url = serializers.URLField(required=False, allow_blank=True, max_length=1000)

    def validate_form_key(self, value):
        return validate_form_key(value)

    def validate_name(self, value):
        return validate_required_text(value, "name")

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate_address(self, value):
        return validate_short_text(value, "address", max_length=20, required=True)

    def validate_notes(self, value):
        return validate_short_text(value, "notes", max_length=20, required=False)

    def validate_submitted_from_url(self, value):
        return validate_url(value, required=False)

    def validate(self, attrs):
        try:
            config = WebsiteFormConfiguration.objects.get(form_key=attrs["form_key"])
        except WebsiteFormConfiguration.DoesNotExist:
            raise serializers.ValidationError({"form_key": "Invalid form key."})
        if not config.is_active:
            raise serializers.ValidationError({"form_key": "This form is not accepting leads right now."})
        attrs["configuration"] = config
        return attrs


class WebsiteLeadListSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    form_title = serializers.CharField(source="form_configuration.form_title", read_only=True)

    class Meta:
        model = WebsiteLead
        fields = [
            "id",
            "customer_name",
            "phone",
            "address",
            "notes",
            "website_name",
            "website_url",
            "form_key",
            "form_title",
            "branch",
            "branch_name",
            "status",
            "routing_status",
            "notification_status",
            "created_at",
        ]


class WebsiteLeadDetailSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    form_title = serializers.CharField(source="form_configuration.form_title", read_only=True)

    class Meta:
        model = WebsiteLead
        fields = "__all__"


class WebsiteLeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteLead
        fields = ["status", "assigned_to"]

    def validate_status(self, value):
        if value not in WebsiteLeadStatus.values:
            raise serializers.ValidationError("Invalid status.")
        return value


class WebsiteLeadAssignSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )


class WebsiteLeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = WebsiteLeadActivity
        fields = [
            "id",
            "lead",
            "form_configuration",
            "action",
            "old_value",
            "new_value",
            "message",
            "created_by",
            "created_by_name",
            "created_at",
            "metadata",
        ]
