# health_project/devices/models.py
from django.db import models
import uuid
from django.conf import settings

class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    token = models.CharField(max_length=128, unique=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
