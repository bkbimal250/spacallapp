from django.db import models
from core.managers.soft_delete_manager import SoftDeleteManager


class SoftDeleteModel(models.Model):
    """
    Soft delete functionality
    """

    is_deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True
