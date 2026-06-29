from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Device, DeviceStorageReport


class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True, allow_null=True)
    branch_is_active = serializers.BooleanField(source='branch.is_active', read_only=True, default=False)

    @extend_schema_field(serializers.CharField())
    def get_status(self, obj):
        return obj.status

    @extend_schema_field(serializers.BooleanField())
    def get_is_online(self, obj):
        return obj.is_online

    status = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    compliance_status = serializers.SerializerMethodField()
    compliance_reason = serializers.SerializerMethodField()
    compliance_followed_up_at = serializers.SerializerMethodField()
    app_version = serializers.SerializerMethodField()
    device_model = serializers.SerializerMethodField()
    manufacturer = serializers.SerializerMethodField()
    fcm_present = serializers.SerializerMethodField()
    pending_call_count = serializers.SerializerMethodField()
    last_sync_error = serializers.SerializerMethodField()
    storage_status = serializers.SerializerMethodField()
    total_app_storage_mb = serializers.SerializerMethodField()
    last_storage_report_at = serializers.SerializerMethodField()
    last_seen_at = serializers.DateTimeField(source="last_heartbeat", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id", "branch", "branch_name", "phone_name", "device_id", "android_id", "registration_token", "sim_1_number", "sim_2_number",
            "last_sync", "last_heartbeat", "last_seen_at", "is_registered", "is_active", "is_blocked",
            "status", "is_online", "created_at", "branch_is_active",
            "compliance_status", "compliance_reason", "compliance_followed_up_at",
            "app_version", "device_model", "manufacturer", "fcm_present",
            "pending_call_count", "last_sync_error",
            "storage_status", "total_app_storage_mb", "last_storage_report_at",
        )

    def get_compliance_status(self, obj):
        state = getattr(obj, "compliance_state", None)
        return state.status if state else "OK"

    def get_compliance_reason(self, obj):
        state = getattr(obj, "compliance_state", None)
        return state.reason if state else ""

    def get_compliance_followed_up_at(self, obj):
        state = getattr(obj, "compliance_state", None)
        return state.followed_up_at if state else None

    def get_app_version(self, obj):
        health = getattr(obj, "health", None)
        return health.app_version if health else None

    def get_device_model(self, obj):
        health = getattr(obj, "health", None)
        return health.device_model if health else None

    def get_manufacturer(self, obj):
        health = getattr(obj, "health", None)
        return health.manufacturer if health else None

    def get_fcm_present(self, obj):
        return bool(obj.fcm_token)

    def get_pending_call_count(self, obj):
        health = getattr(obj, "health", None)
        return health.pending_call_count if health else 0

    def get_last_sync_error(self, obj):
        health = getattr(obj, "health", None)
        return health.last_sync_error if health else ""

    def _latest_storage(self, obj):
        return obj.storage_reports.order_by("-reported_at").first()

    def get_storage_status(self, obj):
        report = self._latest_storage(obj)
        return report.storage_status if report else "NORMAL"

    def get_total_app_storage_mb(self, obj):
        report = self._latest_storage(obj)
        return report.total_app_storage_mb if report else 0

    def get_last_storage_report_at(self, obj):
        report = self._latest_storage(obj)
        return report.reported_at if report else None


class DeviceStorageReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStorageReport
        fields = (
            "total_app_storage_mb", "db_size_mb", "cache_size_mb", "audio_size_mb",
            "log_size_mb", "temp_size_mb", "other_size_mb", "unsynced_call_count",
            "pending_sync_count", "failed_sync_count", "cleanup_deleted_records_count",
            "cleanup_deleted_files_count", "cleanup_freed_mb", "last_cleanup_at",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure branch_name is never None if we want a default string
        if ret.get('branch_name') is None:
            ret['branch_name'] = "Unassigned"
        return ret

class ClaimRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=32, required=True)
    # Optional for backward compatibility: already-deployed Android builds can
    # keep claiming devices with only the one-time registration token.
    android_id = serializers.CharField(max_length=255, required=False, allow_blank=False, trim_whitespace=True)

    def validate_android_id(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("android_id cannot be blank.")
        return normalized


class RestoreRegistrationSerializer(serializers.Serializer):
    android_id = serializers.CharField(max_length=255, required=True, allow_blank=False, trim_whitespace=True)
    old_device_id = serializers.CharField(max_length=255, required=False, allow_blank=True, trim_whitespace=True)
    fcm_token = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    app_version = serializers.CharField(max_length=40, required=False, allow_blank=True, trim_whitespace=True)
    device_model = serializers.CharField(max_length=255, required=False, allow_blank=True, trim_whitespace=True)
    manufacturer = serializers.CharField(max_length=120, required=False, allow_blank=True, trim_whitespace=True)

    def validate_android_id(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("android_id is required.")
        return normalized

