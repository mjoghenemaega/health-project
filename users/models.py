# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.username
