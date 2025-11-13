# health_project/health_project/urls.py
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from measurements import views as meas_views
from devices import urls as device_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", user_views.home_redirect, name="home"),
    path("accounts/login/", user_views.user_login, name="login"),
    path("accounts/logout/", user_views.user_logout, name="logout"),
    path("register/patient/", user_views.register_patient, name="register-patient"),
    path("register/doctor/", user_views.register_doctor, name="register-doctor"),
    path("device/", include(device_urls)),
    path("patient/dashboard/", meas_views.patient_dashboard, name="patient-dashboard"),
    path("doctor/dashboard/", meas_views.doctor_dashboard, name="doctor-dashboard"),
    path('patient/symptom/submit/', meas_views.submit_symptom, name='submit-symptom'),
    # AJAX endpoints for charts / calendar:
    path("api/patient/measurements/", meas_views.patient_measurements_json, name="api-patient-measurements"),
    path("api/doctor/patients/", meas_views.doctor_patients_json, name="api-doctor-patients"),
    path("api/patient/symptoms/", meas_views.patient_symptoms_json, name="patient-symptoms-json"),
    path('patient/menstrual/record/', meas_views.record_menstrual_cycle, name='record-menstrual'),  # Add this line

]
