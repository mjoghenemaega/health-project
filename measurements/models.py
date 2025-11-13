# health_project/measurements/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    assigned_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                      related_name='patients', on_delete=models.SET_NULL)
    last_menstrual_date = models.DateField(null=True, blank=True)
    has_fibroid_history = models.BooleanField(default=False)
    
    @property
    def age(self):
        if self.dob:
            today = timezone.now().date()
            return (today - self.dob).days // 365
        return None

    def __str__(self):
        return self.user.username

class Measurement(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='measurements')
    timestamp = models.DateTimeField()
    heart_rate = models.FloatField(null=True, blank=True)
    spo2 = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    device_id = models.CharField(max_length=128, null=True, blank=True)
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    # Fields for menstrual tracking
    menstrual_pain = models.IntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(11)])  # 0-10 scale
    bleeding_intensity = models.CharField(max_length=10, null=True, blank=True, 
                                       choices=[('light', 'Light'), ('moderate', 'Moderate'), ('heavy', 'Heavy')])
    
    raw_ppg = models.JSONField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ("-timestamp",)

    @property
    def bp_category(self):
        if not (self.systolic_bp and self.diastolic_bp):
            return None
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "Normal"
        elif self.systolic_bp < 130 and self.diastolic_bp < 80:
            return "Elevated"
        elif 130 <= self.systolic_bp < 140 or 80 <= self.diastolic_bp < 90:
            return "Stage 1 Hypertension"
        else:
            return "Stage 2 Hypertension"    

class Symptom(models.Model):
    SYMPTOM_CHOICES = [
        # Existing choices
        ('fever', 'Fever'),
        ('headache', 'Headache'),
        ('fatigue', 'Fatigue'),
        # New choices for fibroid and BP monitoring
        ('heavy_bleeding', 'Heavy Menstrual Bleeding'),
        ('pelvic_pain', 'Pelvic Pain'),
        ('frequent_urination', 'Frequent Urination'),
        ('bloating', 'Abdominal Bloating'),
        ('anemia_symptoms', 'Anemia Symptoms'),
        ('dizziness', 'Dizziness'),
        ('irregular_periods', 'Irregular Periods'),
        ('chest_pain', 'Chest Pain'),
        ('vision_changes', 'Vision Changes'),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='symptoms')
    symptom_type = models.CharField(max_length=50, choices=SYMPTOM_CHOICES)
    severity = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)])  # 1-10 scale
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.username} - {self.get_symptom_type_display()}"

class MenstrualCycle(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='menstrual_cycles')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    cycle_length = models.IntegerField(null=True, blank=True)
    flow_intensity = models.CharField(max_length=10, choices=[
        ('light', 'Light'),
        ('moderate', 'Moderate'),
        ('heavy', 'Heavy')
    ])
    pain_level = models.IntegerField(choices=[(i, str(i)) for i in range(11)])  # 0-10 scale
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.end_date and self.start_date:
            self.cycle_length = (self.end_date - self.start_date).days
        super().save(*args, **kwargs)

# measurements/models.py  (append to existing file)
class ToolTip(models.Model):
    """
    Auto-generated 'tip' or recommendation based on a submitted symptom
    and recent measurement. Not a definitive diagnosis — advise consult.
    """
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="tooltips")
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE, related_name="tooltips", null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.username} - {self.message[:40]}"
    





