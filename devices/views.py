# devices/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from measurements.models import PatientProfile, Measurement,MenstrualCycle
from devices.models import Device
from django.contrib.auth.decorators import login_required


@api_view(['POST'])
@permission_classes([])  # allow unauthenticated — device uses its token header
def ingest(request):
    # Device authentication
    auth = request.headers.get("Authorization","")
    token = None
    if auth.startswith("Device "):
        token = auth.split(" ",1)[1].strip()
    elif auth.startswith("Bearer "):
        token = auth.split(" ",1)[1].strip()
    else:
        return Response({"detail":"Missing device auth"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        device = Device.objects.get(token=token)
    except Device.DoesNotExist:
        return Response({"detail":"Invalid device token"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get patient data
    payload = request.data
    patient_id = payload.get("patient_user_id")
    if not patient_id:
        return Response({"detail":"Missing patient_user_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        patient_profile = PatientProfile.objects.get(user__id=patient_id)
    except PatientProfile.DoesNotExist:
        return Response({"detail":"Patient not found"}, status=status.HTTP_400_BAD_REQUEST)

    # Parse timestamp
    ts = payload.get("timestamp")
    try:
        dt = parse_datetime(ts) if ts else None
        if dt is None:
            dt = timezone.now()
    except:
        dt = timezone.now()

    # Create measurement with MAX30102 data
    try:
        meas = Measurement.objects.create(
            patient=patient_profile,
            timestamp=dt,
            heart_rate=payload.get("heart_rate"),
            spo2=payload.get("spo2"),
            temperature=payload.get("temperature"),
            device_id=str(device.id),
            raw_ppg=payload.get("raw_ppg", None),
            systolic_bp=payload.get("systolic_bp"),  # Optional BP data
            diastolic_bp=payload.get("diastolic_bp"),  # Optional BP data
            note=payload.get("note","")
        )

        # Update device last seen
        device.last_seen = timezone.now()
        device.save(update_fields=["last_seen"])

        # Generate recommendations based on WHO standards
        recs = []
        
        # SpO2 checks
        try:
            if meas.spo2 is not None:
                spo2 = float(meas.spo2)
                if spo2 < 92:
                    recs.append("Low SpO₂ detected — seek medical attention.")
                elif spo2 < 95:
                    recs.append("Borderline SpO₂ — rest and re-check.")
        except:
            pass

        # Heart rate checks
        try:
            if meas.heart_rate is not None:
                hr = float(meas.heart_rate)
                if hr > 120:
                    recs.append("High heart rate — rest and consult doctor if persists.")
                elif hr < 45:
                    recs.append("Low heart rate — seek medical advice.")
        except:
            pass

        # Blood pressure checks
        if meas.systolic_bp and meas.diastolic_bp:
            bp_category = meas.bp_category
            if bp_category == "Stage 2 Hypertension":
                recs.append("HIGH BLOOD PRESSURE ALERT: Seek immediate medical attention.")
            elif bp_category == "Stage 1 Hypertension":
                recs.append("Blood pressure elevated - schedule doctor consultation.")

        return Response({
            "status": "ok",
            "measurement_id": str(meas.id),
            "recommendations": recs
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# New endpoint for menstrual cycle tracking
@api_view(['POST'])
@login_required
def record_menstrual_cycle(request):
    """
    Record menstrual cycle data for female patients
    """
    if not request.user.is_patient:
        return Response({"error": "Patients only"}, status=status.HTTP_403_FORBIDDEN)
        
    profile = PatientProfile.objects.get(user=request.user)
    if profile.gender != 'F':
        return Response({"error": "Feature available for female patients only"}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cycle = MenstrualCycle.objects.create(
            patient=profile,
            start_date=request.data['start_date'],
            flow_intensity=request.data['flow_intensity'],
            pain_level=int(request.data['pain_level']),
            notes=request.data.get('notes', '')
        )
        
        return Response({
            "status": "success",
            "cycle_id": cycle.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)