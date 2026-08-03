from django.db import models

from core.models import TimeStampedModel


class DashboardStatistic(TimeStampedModel):
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="dashboard_statistics",
        null=True,
        blank=True,
    )
    date = models.DateField(db_index=True)
    incoming = models.PositiveIntegerField(default=0)
    outgoing = models.PositiveIntegerField(default=0)
    missed = models.PositiveIntegerField(default=0)
    total_calls = models.PositiveIntegerField(default=0)
    active_devices = models.PositiveIntegerField(default=0)
    total_devices = models.PositiveIntegerField(default=0)
    total_contacts = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    total_leads = models.PositiveIntegerField(default=0)
    total_exports = models.PositiveIntegerField(default=0)
    avg_duration = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)

    class Meta:
        db_table = "dashboard_statistics"
        constraints = [
            models.UniqueConstraint(fields=["branch", "date"], name="uniq_dashboard_stat_branch_date"),
        ]
        indexes = [
            models.Index(fields=["date", "branch"], name="dash_stat_date_branch_idx"),
            models.Index(fields=["branch", "-date"], name="dash_stat_branch_date_desc_idx"),
        ]

    def __str__(self):
        branch_name = self.branch.spa_name if self.branch else "All branches"
        return f"{branch_name} - {self.date}"
