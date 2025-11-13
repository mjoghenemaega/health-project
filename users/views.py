# health_project/users/views.py
from django.shortcuts import render, redirect
from .forms import PatientSignUpForm, DoctorSignUpForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from measurements.models import PatientProfile

def register_patient(request):
    if request.method == "POST":
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create PatientProfile with gender
            PatientProfile.objects.create(
                user=user,
                gender=user.gender  # Make sure this matches
            )
            login(request, user)
            return redirect("patient-dashboard")
    else:
        form = PatientSignUpForm()
    return render(request, "users/register_patient.html", {"form": form})

def register_doctor(request):
    if request.method == "POST":
        form = DoctorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("doctor-dashboard")
    else:
        form = DoctorSignUpForm()
    return render(request, "users/register_doctor.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_doctor:
                return redirect("doctor-dashboard")
            return redirect("patient-dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect("login")



from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor-dashboard')
        return redirect('patient-dashboard')
    return redirect('login')
