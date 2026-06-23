import re
import unicodedata

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from core.models import BaseModel, SoftDeleteModel, TimeStampedModel


def normalize_location_name(value: str | None) -> str:
    """
    Normalize location/city/area/group/alias text for matching.

    Examples:
    NAVI MUMBAI -> navi mumbai
    CBD-Belapur -> cbd belapur
    Panvel   To  Seawoods -> panvel to seawoods
    """
    if not value:
        return ""

    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKC", value)

    # Convert separators to spaces.
    value = re.sub(r"[-_/|,.;:]+", " ", value)

    # Keep unicode word chars, Hindi range, and spaces.
    value = re.sub(r"[^\w\s\u0900-\u097F]", "", value, flags=re.UNICODE)

    # Collapse spaces.
    value = re.sub(r"\s+", " ", value).strip()

    return value


class LocationBaseModel(BaseModel, TimeStampedModel, SoftDeleteModel):
    """
    Common base for locations app.

    If your BaseModel already includes created_at/updated_at/is_deleted,
    then change this inheritance to:
        class LocationBaseModel(BaseModel):
    """

    class Meta:
        abstract = True


class State(LocationBaseModel):
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=140, editable=False, db_index=True)
    slug = models.SlugField(max_length=160, allow_unicode=True, blank=True, db_index=True)
    code = models.CharField(max_length=20, blank=True, null=True, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["priority", "name"]
        verbose_name = "State"
        verbose_name_plural = "States"
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_name"],
                condition=Q(is_deleted=False),
                name="locations_state_unique_active_normalized_name",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "priority"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["code"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_location_name(self.name)
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or self.normalized_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class City(LocationBaseModel):
    state = models.ForeignKey(
        State,
        on_delete=models.PROTECT,
        related_name="cities",
    )
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=140, editable=False, db_index=True)
    slug = models.SlugField(max_length=160, allow_unicode=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["state__name", "priority", "name"]
        verbose_name = "City"
        verbose_name_plural = "Cities"
        constraints = [
            models.UniqueConstraint(
                fields=["state", "normalized_name"],
                condition=Q(is_deleted=False),
                name="locations_city_unique_active_state_normalized_name",
            ),
        ]
        indexes = [
            models.Index(fields=["state", "is_active"]),
            models.Index(fields=["state", "priority"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_location_name(self.name)
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or self.normalized_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class CityAlias(LocationBaseModel):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    alias = models.CharField(max_length=160)
    normalized_alias = models.CharField(max_length=180, editable=False, db_index=True)
    language = models.CharField(max_length=30, blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["city__state__name", "city__name", "alias"]
        verbose_name = "City Alias"
        verbose_name_plural = "City Aliases"
        constraints = [
            models.UniqueConstraint(
                fields=["city", "normalized_alias"],
                condition=Q(is_deleted=False),
                name="locations_cityalias_unique_active_city_alias",
            ),
        ]
        indexes = [
            models.Index(fields=["normalized_alias"]),
            models.Index(fields=["city", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_alias = normalize_location_name(self.alias)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias} → {self.city.name}"


class LocationGroup(LocationBaseModel):
    """
    Group/zone inside a city.

    Example:
    State: Maharashtra
    City: Navi Mumbai
    Group: Panvel To Seawoods
    Areas: Panvel, Kharghar, Belapur, Seawoods
    """

    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="location_groups",
    )
    name = models.CharField(max_length=160)
    normalized_name = models.CharField(max_length=180, editable=False, db_index=True)
    slug = models.SlugField(max_length=200, allow_unicode=True, blank=True, db_index=True)

    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["city__state__name", "city__name", "priority", "name"]
        verbose_name = "Location Group"
        verbose_name_plural = "Location Groups"
        constraints = [
            models.UniqueConstraint(
                fields=["city", "normalized_name"],
                condition=Q(is_deleted=False),
                name="locations_group_unique_active_city_normalized_name",
            ),
        ]
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["city", "priority"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_location_name(self.name)
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or self.normalized_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.city.name}"


class Area(LocationBaseModel):
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="areas",
    )
    name = models.CharField(max_length=140)
    normalized_name = models.CharField(max_length=160, editable=False, db_index=True)
    slug = models.SlugField(max_length=180, allow_unicode=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["city__state__name", "city__name", "priority", "name"]
        verbose_name = "Area"
        verbose_name_plural = "Areas"
        constraints = [
            models.UniqueConstraint(
                fields=["city", "normalized_name"],
                condition=Q(is_deleted=False),
                name="locations_area_unique_active_city_normalized_name",
            ),
        ]
        indexes = [
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["city", "priority"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_location_name(self.name)
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or self.normalized_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.city.name}"


class AreaAlias(LocationBaseModel):
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    alias = models.CharField(max_length=180)
    normalized_alias = models.CharField(max_length=200, editable=False, db_index=True)
    language = models.CharField(max_length=30, blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["area__city__state__name", "area__city__name", "area__name", "alias"]
        verbose_name = "Area Alias"
        verbose_name_plural = "Area Aliases"
        constraints = [
            models.UniqueConstraint(
                fields=["area", "normalized_alias"],
                condition=Q(is_deleted=False),
                name="locations_areaalias_unique_active_area_alias",
            ),
        ]
        indexes = [
            models.Index(fields=["normalized_alias"]),
            models.Index(fields=["area", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_alias = normalize_location_name(self.alias)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias} → {self.area.name}"


class LocationGroupArea(LocationBaseModel):
    group = models.ForeignKey(
        LocationGroup,
        on_delete=models.CASCADE,
        related_name="group_areas",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name="area_groups",
    )

    is_primary = models.BooleanField(default=False, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["group__city__name", "group__priority", "priority", "area__name"]
        verbose_name = "Location Group Area"
        verbose_name_plural = "Location Group Areas"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "area"],
                condition=Q(is_deleted=False),
                name="locations_grouparea_unique_active_group_area",
            ),
        ]
        indexes = [
            models.Index(fields=["group", "priority"]),
            models.Index(fields=["area"]),
            models.Index(fields=["is_primary"]),
        ]

    def clean(self):
        super().clean()

        if self.group_id and self.area_id and self.group.city_id != self.area.city_id:
            raise ValidationError(
                {
                    "area": "Selected area must belong to the same city as the selected location group."
                }
            )

    def __str__(self):
        return f"{self.group.name} → {self.area.name}"


class BranchCoverageArea(LocationBaseModel):
    """
    Flexible mapping between existing Spa/Branch model and location areas.

    GenericForeignKey is used because existing branch/spa model name may differ.
    Later, if you confirm exact model, you can replace this with direct FK.
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="location_branch_coverages",
    )
    object_id = models.CharField(max_length=64, db_index=True)
    branch = GenericForeignKey("content_type", "object_id")

    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="branch_coverages",
    )
    location_group = models.ForeignKey(
        LocationGroup,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="branch_coverages",
    )

    is_primary = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveIntegerField(default=0, db_index=True)

    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["priority", "area__city__name", "area__name"]
        verbose_name = "Branch Coverage Area"
        verbose_name_plural = "Branch Coverage Areas"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "area"],
                condition=Q(is_deleted=False),
                name="locations_branchcoverage_unique_active_branch_area",
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["area", "is_active"]),
            models.Index(fields=["location_group", "is_active"]),
            models.Index(fields=["is_primary"]),
        ]

    def clean(self):
        super().clean()

        if (
            self.location_group_id
            and self.area_id
            and self.location_group.city_id != self.area.city_id
        ):
            raise ValidationError(
                {
                    "location_group": "Location group must belong to the same city as the selected area."
                }
            )

    def __str__(self):
        return f"{self.branch} → {self.area.name}"


class LocationMatchIgnorePhrase(LocationBaseModel):
    """
    Phrases that should never be treated as city/area.

    Examples:
    hi, hello, hy, नमस्ते, more info, job chahiye, हिंदी में मैसेज कीजिए
    """

    class PhraseType(models.TextChoices):
        GREETING = "greeting", "Greeting"
        GENERAL = "general", "General"
        JOB = "job", "Job Inquiry"
        SERVICE = "service", "Service Inquiry"
        OTHER = "other", "Other"

    phrase = models.CharField(max_length=180)
    normalized_phrase = models.CharField(max_length=200, editable=False, db_index=True)
    phrase_type = models.CharField(
        max_length=30,
        choices=PhraseType.choices,
        default=PhraseType.GENERAL,
        db_index=True,
    )

    language = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["phrase_type", "phrase"]
        verbose_name = "Location Match Ignore Phrase"
        verbose_name_plural = "Location Match Ignore Phrases"
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_phrase", "phrase_type"],
                condition=Q(is_deleted=False),
                name="locations_ignorephrase_unique_active_phrase_type",
            ),
        ]
        indexes = [
            models.Index(fields=["normalized_phrase"]),
            models.Index(fields=["phrase_type", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_phrase = normalize_location_name(self.phrase)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phrase} ({self.phrase_type})"