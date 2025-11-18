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
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.is_doctor = True  # Set is_doctor flag
        
        if commit:
            user.save()
        return user