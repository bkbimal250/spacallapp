from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Base abstract model for all tables
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
