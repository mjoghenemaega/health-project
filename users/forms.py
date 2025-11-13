# health_project/users/forms.py
from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class PatientSignUpForm(UserCreationForm):
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "gender")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_patient = True
        user.gender = self.cleaned_data.get('gender')
        if commit:
            user.save()
        return user

class DoctorSignUpForm(UserCreationForm):
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "gender")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_doctor = True
        user.gender = self.cleaned_data.get('gender')
        if commit:
            user.save()
        return user