# health_project/measurements/admin.py

from django.contrib import admin
from .models import PatientProfile, Measurement, Symptom
admin.site.register(PatientProfile)
admin.site.register(Measurement)
admin.site.register(Symptom)
