# health_project/devices/urls.py
from django.urls import path
from .views import ingest
urlpatterns = [
    path("ingest/", ingest, name="device-ingest"),
]
