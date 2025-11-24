# health_project/measurements/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PatientProfile, Measurement, Symptom, MenstrualCycle
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages



@login_required
def patient_dashboard(request):
    if not request.user.is_patient:
        return redirect("doctor-dashboard")
    profile = PatientProfile.objects.filter(user=request.user).first()
    # print(f"User gender: {profile.gender if profile else 'No profile'}")
    
    latest = profile.measurements.first() if profile else None
    recommendations = []
    if latest:
        if latest.spo2 is not None and latest.spo2 < 95:
            recommendations.append("Re-check SpO₂ in 30 mins; rest.")
        if latest.heart_rate is not None and (latest.heart_rate > 100 or latest.heart_rate < 50):
            recommendations.append("Unusual heart rate — contact your doctor if persistent.")

    if latest:
        # Blood Pressure Recommendations
        if latest.systolic_bp and latest.diastolic_bp:
            bp_category = latest.bp_category
            if bp_category == "Stage 2 Hypertension":
                recommendations.append("HIGH BLOOD PRESSURE ALERT: Seek immediate medical attention.")
            elif bp_category == "Stage 1 Hypertension":
                recommendations.append("Blood pressure elevated - schedule doctor consultation.")

        # Fibroid/Menstrual Monitoring (for female patients)
        if profile.gender == 'F':
            latest_cycle = profile.menstrual_cycles.order_by('-start_date').first()
            if latest_cycle and latest_cycle.flow_intensity == 'heavy':
                recommendations.append("Heavy menstrual bleeding detected - monitor for anemia symptoms.")
            
            if latest_cycle and latest_cycle.pain_level >= 8:
                recommendations.append("Severe menstrual pain reported - consider medical evaluation.")

    # Add symptoms + latest tooltip to context
    recent_symptoms = profile.symptoms.order_by('-created_at')[:10] if profile else []
    latest_tooltip = profile.tooltips.order_by('-created_at').first() if profile else None

    context = {
        "profile": profile,
        "latest": latest,
        "recommendations": recommendations,
        "recent_symptoms": profile.symptoms.order_by('-created_at')[:10] if profile else [],
        "menstrual_data": profile.menstrual_cycles.order_by('-start_date')[:3] if profile and profile.gender == 'F' else None,
        "latest_tooltip": latest_tooltip,
        "show_menstrual": profile.gender == 'F' if profile else False,  # Add this explicit flag
    }
    
    # Debug print - remove after testing
    # print(f"Menstrual data: {context['menstrual_data']}")
    # print(f"Show menstrual: {context['show_menstrual']}")
    
    return render(request, "measurements/patient_dashboard.html", context)



@login_required
def doctor_dashboard(request):
    if not request.user.is_doctor:
        return redirect("patient-dashboard")

    patients = PatientProfile.objects.filter(assigned_doctor=request.user).select_related("user")
    data = []
    for p in patients:
        latest = p.measurements.first()
        condition = "Stable"
        alerts = []

        if latest:
            # Check vitals
            if latest.spo2 and latest.spo2 < 94:
                condition = "Low SpO₂"
                alerts.append("Low oxygen saturation")
            elif latest.heart_rate and (latest.heart_rate < 50 or latest.heart_rate > 110):
                condition = "Abnormal HR"
                alerts.append("Abnormal heart rate")
            
            # Check blood pressure
            if latest.systolic_bp and latest.diastolic_bp:
                if latest.bp_category == "Stage 2 Hypertension":
                    condition = "Severe HTN"
                    alerts.append("Stage 2 Hypertension")
                elif latest.bp_category == "Stage 1 Hypertension":
                    condition = "Stage 1 HTN"
                    alerts.append("Stage 1 Hypertension")

        # Check menstrual data for female patients
        if p.gender == 'F':
            latest_cycle = p.menstrual_cycles.order_by('-start_date').first()
            if latest_cycle:
                if latest_cycle.flow_intensity == 'heavy':
                    alerts.append("Heavy menstrual bleeding")
                if latest_cycle.pain_level >= 8:
                    alerts.append("Severe menstrual pain")
        last_seen = None
        if latest and latest.timestamp:
            last_seen = {
                'date': latest.timestamp.strftime("%b %d, %Y"),
                'time': latest.timestamp.strftime("%H:%M")
            }
        data.append({
            "user_id": str(p.user.id),
            "username": p.user.username,
            "full_name": f"{p.user.first_name} {p.user.last_name}",
            "phone": getattr(p.user, "phone", "N/A"),
            "latest_hr": latest.heart_rate if latest else None,
            "latest_spo2": latest.spo2 if latest else None,
            "latest_temp": latest.temperature if latest else None,
            "latest_bp": f"{latest.systolic_bp}/{latest.diastolic_bp}" if latest and latest.systolic_bp and latest.diastolic_bp else None,
            "bp_category": latest.bp_category if latest and latest.systolic_bp and latest.diastolic_bp else None,
            "last_seen": last_seen,
            "condition": condition,
            "alerts": alerts,
            "gender": p.gender
        })

    return render(request, "measurements/doctor_dashboard.html", {"patients": data})

# @login_required
# def patient_measurements_json(request):
#     if request.user.is_doctor:
#         # doctor must pass ?patient_id=
#         pid = request.GET.get("patient_id")
#         if not pid:
#             return JsonResponse({"error":"patient_id required"}, status=400)
#         try:
#             profile = PatientProfile.objects.get(user__id=pid, assigned_doctor=request.user)
#         except PatientProfile.DoesNotExist:
#             return JsonResponse({"error":"not found"}, status=404)
#     else:
#         profile = PatientProfile.objects.filter(user=request.user).first()
#         if not profile:
#             return JsonResponse({"error":"profile not found"}, status=404)

#     qs = profile.measurements.all()[:500]
#     data = [{"timestamp":m.timestamp.isoformat(), "heart_rate":m.heart_rate, "spo2":m.spo2, "temperature":m.temperature, "id":m.id} for m in qs]
#     return JsonResponse(data, safe=False)
@login_required
def patient_measurements_json(request):
    if request.user.is_doctor:
        pid = request.GET.get("patient_id")
        if not pid:
            return JsonResponse({"error":"patient_id required"}, status=400)
        try:
            profile = PatientProfile.objects.get(user__id=pid, assigned_doctor=request.user)
        except PatientProfile.DoesNotExist:
            return JsonResponse({"error":"not found"}, status=404)
    else:
        profile = PatientProfile.objects.filter(user=request.user).first()
        if not profile:
            return JsonResponse({"error":"profile not found"}, status=404)

    qs = profile.measurements.all()[:500]
    data = [{
        "timestamp": m.timestamp.isoformat(),
        "heart_rate": m.heart_rate,
        "spo2": m.spo2,
        "temperature": m.temperature,
        "systolic_bp": m.systolic_bp,
        "diastolic_bp": m.diastolic_bp,
        "bp_category": m.bp_category,
        "id": m.id
    } for m in qs]
    return JsonResponse(data, safe=False)
@login_required
def doctor_patients_json(request):
    if not request.user.is_doctor:
        return JsonResponse({"error":"for doctors only"}, status=403)
    patients = PatientProfile.objects.filter(assigned_doctor=request.user).select_related("user")
    data = []
    for p in patients:
        latest = p.measurements.first()
        data.append({
            "user_id": str(p.user.id),
            "username": p.user.username,
            "full_name": f"{p.user.first_name} {p.user.last_name}",
            "latest_hr": latest.heart_rate if latest else None,
            "latest_spo2": latest.spo2 if latest else None,
            "latest_temp": latest.temperature if latest else None,
            "last_seen": latest.timestamp.isoformat() if latest else None
        })
    return JsonResponse(data, safe=False)

from .models import Symptom, ToolTip  # add ToolTip import at top with your other imports

@require_POST
@login_required
def submit_symptom(request):
    """
    Accepts a selected symptom from the patient (not free text).
    Creates a Symptom record, then generates a ToolTip (auto recommendation)
    based on the symptom + the latest measurement for that patient.
    """
    if not request.user.is_patient:
        return JsonResponse({"error":"patients only"}, status=403)

    symptom_type = request.POST.get("symptom_type", "").strip()
    try:
        severity = int(request.POST.get("severity", 1))
        if not (1 <= severity <= 10):
            raise ValueError("Severity must be between 1 and 10")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("patient-dashboard")

    profile = PatientProfile.objects.get(user=request.user)

    if not symptom_type:
        messages.error(request, "Please select a symptom before submitting.")
        return redirect("patient-dashboard")

    # Create the Symptom (choice-based)
    symptom = Symptom.objects.create(
        patient=profile, 
        symptom_type=symptom_type,
        severity=severity  # Add this line to include severity
    )

    # Fetch latest measurement (if any)
    latest = profile.measurements.first()

    # Generate a safe, conservative tooltip message (NOT a formal diagnosis)
    message = "Monitor your symptoms and follow up with your doctor if things worsen."

    # Symptom logic — conservative recommendations
    if symptom_type == "fever":
        # if we have temperature data, use it
        if latest and latest.temperature:
            try:
                temp = float(latest.temperature)
                if temp >= 38.5:
                    message = "High temperature recorded (≥38.5°C). Rest, stay hydrated, consider antipyretic, and contact your healthcare provider."
                elif temp >= 37.5:
                    message = "Mild fever recorded. Rest, hydrate, and re-check temperature in 2–3 hours."
                else:
                    message = "Fever reported but latest temperature is normal. Re-check temperature and monitor."
            except:
                message = "Fever reported — monitor temperature regularly and rest."
        else:
            message = "Fever reported — monitor temperature regularly, rest, and stay hydrated."

    elif symptom_type == "headache":
        message = "Headache reported. Rest in a quiet, dim room, stay hydrated. Seek help if severe or sudden."

    elif symptom_type == "fatigue":
        if latest and latest.heart_rate and latest.heart_rate > 100:
            message = "Fatigue with elevated heart rate. Rest, avoid strenuous activity, and contact your doctor if it continues."
        else:
            message = "Fatigue reported. Ensure adequate sleep and hydration; contact your clinician if persistent."

    elif symptom_type == "chest_pain":
        # chest pain is urgent — check SpO2/HR if available
        if latest and latest.spo2 and latest.spo2 < 94:
            message = "Chest pain with low SpO₂ detected. Seek urgent medical attention (call emergency services)."
        else:
            message = "Chest pain reported — seek immediate medical attention."

    elif symptom_type == "shortness_of_breath":
        if latest and latest.spo2 and latest.spo2 < 94:
            message = "Shortness of breath with low SpO₂. Seek urgent medical care."
        else:
            message = "Shortness of breath reported. Sit upright, try controlled breathing. Seek care if it worsens."

    elif symptom_type == "cough":
        message = "Cough reported. Monitor for fever and breathing difficulty. Seek medical advice if cough is persistent or severe."

    elif symptom_type == "dizziness" or symptom_type == "nausea":
        message = "Dizziness/nausea reported. Sit or lie down safely, sip water. Seek help if you faint or symptoms get worse."

    # Save tooltip
    ToolTip.objects.create(patient=profile, symptom=symptom, message=message)

    messages.success(request, "Symptom recorded. Recommendation generated.")
    return redirect("patient-dashboard")

@login_required
def patient_symptoms_json(request):
    if request.user.is_doctor:
        pid = request.GET.get("patient_id")
        if not pid:
            return JsonResponse({"error": "patient_id required"}, status=400)
        try:
            profile = PatientProfile.objects.get(user__id=pid, assigned_doctor=request.user)
        except PatientProfile.DoesNotExist:
            return JsonResponse({"error": "not found"}, status=404)
    else:
        profile = PatientProfile.objects.filter(user=request.user).first()
    qs = profile.symptoms.all().order_by('-created_at')[:20]
    data = [{"symptom_type": s.get_symptom_type_display(), "created_at": s.created_at} for s in qs]
    return JsonResponse(data, safe=False)


@require_POST
@login_required
def record_menstrual_cycle(request):
    """Record menstrual cycle data for female patients"""
    if not request.user.is_patient:
        messages.error(request, "This feature is only available for patients.")
        return redirect("patient-dashboard")
        
    profile = PatientProfile.objects.get(user=request.user)
    if profile.gender != 'F':
        messages.error(request, "Menstrual tracking is only available for female patients.")
        return redirect("patient-dashboard")
    
    try:
        # Validate form data
        start_date = request.POST.get('start_date')
        flow_intensity = request.POST.get('flow_intensity')
        try:
            pain_level = int(request.POST.get('pain_level', 0))
            if not (0 <= pain_level <= 10):
                raise ValueError("Pain level must be between 0 and 10")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("patient-dashboard")

        if not start_date or not flow_intensity:
            messages.error(request, "Please fill in all required fields.")
            return redirect("patient-dashboard")

        # Create menstrual cycle record
        cycle = MenstrualCycle.objects.create(
            patient=profile,
            start_date=start_date,
            flow_intensity=flow_intensity,
            pain_level=pain_level,
            notes=request.POST.get('notes', '')
        )

        # Generate recommendation based on data
        if flow_intensity == 'heavy':
            message = "Heavy flow reported. Monitor for signs of anemia and rest adequately."
        elif pain_level >= 8:
            message = "Severe menstrual pain reported. Consider pain management and consult your doctor."
        else:
            message = "Menstrual cycle recorded. Track any changes in flow or pain levels."

        # Create tooltip
        ToolTip.objects.create(
            patient=profile,
            message=message
        )
        
        messages.success(request, "Menstrual cycle data recorded successfully.")
        return redirect("patient-dashboard")
        
    except Exception as e:
        messages.error(request, f"Error recording menstrual data: {str(e)}")
        return redirect("patient-dashboard")
    



@login_required
def patient_menstrual_json(request):
    if request.user.is_doctor:
        pid = request.GET.get("patient_id")
        if not pid:
            return JsonResponse({"error": "patient_id required"}, status=400)
        try:
            profile = PatientProfile.objects.get(user__id=pid, assigned_doctor=request.user)
        except PatientProfile.DoesNotExist:
            return JsonResponse({"error": "not found"}, status=404)
    else:
        profile = PatientProfile.objects.filter(user=request.user).first()
    
    if not profile:
        return JsonResponse([], safe=False)
    
    qs = profile.menstrual_cycles.all().order_by('-start_date')[:10]
    data = [{
        "start_date": m.start_date.isoformat() if m.start_date else None,
        "end_date": m.end_date.isoformat() if m.end_date else None,
        "flow_intensity": m.flow_intensity,
        "pain_level": m.pain_level,
        "notes": m.notes
    } for m in qs]
    return JsonResponse(data, safe=False)