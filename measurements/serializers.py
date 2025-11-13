# measurements/serializers.py

from rest_framework import serializers
from .models import Measurement, Symptom, PatientProfile

class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ['id', 'timestamp', 'heart_rate', 'spo2', 'temperature']

class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ['id', 'symptom_type', 'created_at']
