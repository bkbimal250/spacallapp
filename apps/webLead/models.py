from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models.base import BaseModel
from core.models.timestamped import TimeStampedModel


class WebsiteLeadStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CONVERTED = "converted", "Converted"
    REJECTED = "rejected", "Rejected"
    DUPLICATE = "duplicate", "Duplicate"


class WebsiteLeadRoutingStatus(models.TextChoices):
    ROUTED = "routed", "Routed"
    PENDING_CONFIGURATION = "pending_configuration", "Pending Configuration"
    UNASSIGNED = "unassigned", "Unassigned"


class WebsiteLeadNotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    NOT_REQUIRED = "not_required", "Not Required"


class WebsiteFormConfiguration(BaseModel, TimeStampedModel):
    THEME_CHOICES = (
        ("light", "Light"),
        ("dark", "Dark"),
        ("custom", "Custom"),
    )

    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="website_form_configurations",
        help_text="Spa branch where leads from this website form should route.",
    )
    website_name = models.CharField(max_length=150, db_index=True)
    website_url = models.URLField(max_length=500)
    form_key = models.CharField(max_length=80, unique=True, db_index=True)
    form_title = models.CharField(max_length=150, default="Book Appointment")

    primary_color = models.CharField(max_length=20, default="#BD9B5F")
    background_color = models.CharField(max_length=20, default="#FFFFFF")
    button_color = models.CharField(max_length=20, default="#25D366")
    text_color = models.CharField(max_length=20, default="#111111")
    border_radius = models.CharField(max_length=20, default="16px")
    font_family = models.CharField(max_length=100, default="Inter")
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default="light")

    submit_button_text = models.CharField(max_length=80, default="Submit")
    success_message = models.CharField(
        max_length=255,
        default="Thank you. Our team will contact you shortly.",
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_website_form_configurations",
    )

    class Meta:
        db_table = "website_form_configurations"
        ordering = ["website_name"]
        indexes = [
            models.Index(fields=["branch", "is_active"]),
            models.Index(fields=["website_name"]),
            models.Index(fields=["website_url"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Website Form Configuration"
        verbose_name_plural = "Website Form Configurations"

    def save(self, *args, **kwargs):
        if not self.form_key:
            from .services import generate_form_key

            self.form_key = generate_form_key(self.website_name)
        super().save(*args, **kwargs)

    def __str__(self):
        branch_name = self.branch.spa_name if self.branch else "Unassigned"
        return f"{self.website_name} ({self.form_key}) - {branch_name}"


class WebsiteLead(BaseModel, TimeStampedModel):
    form_configuration = models.ForeignKey(
        WebsiteFormConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="website_leads",
    )
    website_name = models.CharField(max_length=150, db_index=True)
    website_url = models.URLField(max_length=500)
    form_key = models.CharField(max_length=80, db_index=True)

    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, db_index=True)
    address = models.CharField(max_length=20)
    notes = models.CharField(max_length=20, blank=True)

    submitted_from_url = models.URLField(max_length=1000, blank=True)
    referrer_url = models.URLField(max_length=1000, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=WebsiteLeadStatus.choices,
        default=WebsiteLeadStatus.NEW,
        db_index=True,
    )
    routing_status = models.CharField(
        max_length=40,
        choices=WebsiteLeadRoutingStatus.choices,
        default=WebsiteLeadRoutingStatus.UNASSIGNED,
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_website_leads",
    )

    notification_status = models.CharField(
        max_length=20,
        choices=WebsiteLeadNotificationStatus.choices,
        default=WebsiteLeadNotificationStatus.PENDING,
        db_index=True,
    )
    notification_error = models.TextField(blank=True)

    contacted_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "website_leads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["branch", "created_at"]),
            models.Index(fields=["form_key", "phone", "created_at"]),
            models.Index(fields=["website_name", "created_at"]),
            models.Index(fields=["status", "routing_status"]),
            models.Index(fields=["notification_status"]),
        ]
        verbose_name = "Website Lead"
        verbose_name_plural = "Website Leads"

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.status == WebsiteLeadStatus.CONTACTED and not self.contacted_at:
            self.contacted_at = now
        elif self.status == WebsiteLeadStatus.CONVERTED and not self.converted_at:
            self.converted_at = now
        elif self.status == WebsiteLeadStatus.REJECTED and not self.rejected_at:
            self.rejected_at = now
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.phone} from {self.website_name}"


class WebsiteLeadActivity(BaseModel):
    lead = models.ForeignKey(
        WebsiteLead,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    form_configuration = models.ForeignKey(
        WebsiteFormConfiguration,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    action = models.CharField(max_length=80, db_index=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="website_lead_activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "website_lead_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["lead", "created_at"]),
            models.Index(fields=["form_configuration", "created_at"]),
        ]
        verbose_name = "Website Lead Activity"
        verbose_name_plural = "Website Lead Activities"

    def __str__(self):
        return f"{self.action} at {self.created_at:%Y-%m-%d %H:%M}"


class WebsiteFormDailyStats(BaseModel):
    date = models.DateField(db_index=True)
    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="website_form_daily_stats",
    )
    website_name = models.CharField(max_length=150, db_index=True)
    website_url = models.URLField(max_length=500)
    form_key = models.CharField(max_length=80, db_index=True)
    total_submissions = models.PositiveIntegerField(default=0)
    successful_submissions = models.PositiveIntegerField(default=0)
    duplicate_submissions = models.PositiveIntegerField(default=0)
    rejected_submissions = models.PositiveIntegerField(default=0)
    converted_count = models.PositiveIntegerField(default=0)
    notification_sent_count = models.PositiveIntegerField(default=0)
    notification_failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "website_form_daily_stats"
        unique_together = ("date", "branch", "form_key")
        ordering = ["-date", "website_name"]
        indexes = [
            models.Index(fields=["date", "branch"]),
            models.Index(fields=["date", "website_name"]),
            models.Index(fields=["date", "form_key"]),
        ]
        verbose_name = "Website Form Daily Stat"
        verbose_name_plural = "Website Form Daily Stats"

    def __str__(self):
        return f"{self.date} - {self.website_name} - {self.total_submissions}"
