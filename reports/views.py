import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ReportCard, DoctorRecommendation
from .serializers import ReportCardSerializer, DoctorRecommendationSerializer
from doctors.models import Doctor
from health.models import HealthRecord, Prediction
from health.ocr_processor import VitalSignExtractor
from health.ml_model import predictor


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_nearby_doctors(patient, specialist=None, radius=50):
    """Get nearby doctors based on patient location."""
    if not patient.latitude or not patient.longitude:
        return []
    
    all_doctors = Doctor.objects.filter(is_available=True)
    if specialist:
        all_doctors = all_doctors.filter(specialization=specialist)
    
    nearby = []
    for doctor in all_doctors:
        if doctor.latitude and doctor.longitude:
            distance = haversine(patient.latitude, patient.longitude, doctor.latitude, doctor.longitude)
            if distance <= radius:
                doctor.distance = round(distance, 1)
                nearby.append(doctor)
    
    # Sort by rating first, then distance
    nearby.sort(key=lambda x: (-x.rating, x.distance))
    return nearby


SPECIALIST_MAP = {
    'Cardiologist': ['Cardiologist'],
    'Pulmonologist': ['Pulmonologist'],
    'Endocrinologist': ['Endocrinologist'],
    'Neurologist': ['Neurologist'],
    'General Physician': ['General Physician', 'Cardiologist'],
}


def get_recommended_doctors(patient, report):
    """Recommend doctors based on latest health prediction."""
    specialist = None
    try:
        latest = HealthRecord.objects.filter(user=patient).select_related('prediction').first()
        if latest and hasattr(latest, 'prediction'):
            specialist = latest.prediction.specialist_needed
    except Exception:
        pass

    specializations = SPECIALIST_MAP.get(specialist, ['General Physician'])
    DoctorRecommendation.objects.filter(report=report).delete()

    recommendations = []
    for i, spec in enumerate(specializations):
        doctors = Doctor.objects.filter(specialization=spec, is_available=True).order_by('-rating')[:3]
        for doc in doctors:
            score = 100 - (i * 10) + doc.rating
            reason = f"Recommended based on your health analysis. Specialization in {spec} matches your current health needs."
            rec = DoctorRecommendation.objects.create(
                report=report, doctor=doc, reason=reason, match_score=score
            )
            recommendations.append(rec)
    return recommendations


# ─── Web Views ───────────────────────────────────────────────────────────────

@login_required
def report_upload(request):
    """Upload medical report, extract vital signs, and get doctor recommendations"""
    if request.method == 'POST':
        title = request.POST.get('title', 'Medical Report')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, 'Please select a file to upload.')
            return render(request, 'reports/upload.html')
        
        # Create report
        report = ReportCard.objects.create(
            patient=request.user, 
            title=title,
            description=description, 
            file=file
        )
        
        print(f"\n{'='*70}")
        print(f"📋 PROCESSING UPLOADED REPORT")
        print(f"  Patient: {request.user.username}")
        print(f"  Title: {title}")
        print(f"  File: {file.name}")
        print(f"{'='*70}\n")
        
        # Extract vital signs from the report file
        vital_signs = None
        file_path = report.file.path
        
        print(f"🔍 Step 1: Extracting vital signs from report...")
        try:
            vital_signs = VitalSignExtractor.extract_from_file(file_path)
        except Exception as e:
            print(f"   ⚠️  OCR extraction error: {str(e)}")
        
        # If extraction failed, use defaults (only if manual values provided)
        if not vital_signs:
            print(f"   Using default or manual vital signs...")
            # Helper function to get float value with fallback
            def get_float_value(key, default):
                val = request.POST.get(key, '').strip()
                if val:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default
                return default
            
            vital_signs = {
                'heart_rate': get_float_value('heart_rate', 75.0),
                'blood_pressure_sys': get_float_value('blood_pressure_sys', 120.0),
                'blood_pressure_dia': get_float_value('blood_pressure_dia', 80.0),
                'spo2': get_float_value('spo2', 98.0),
                'bmi': get_float_value('bmi', 22.0),
                'temperature': get_float_value('temperature', 36.5),
                'glucose': get_float_value('glucose', 95.0),
            }
        
        print(f"\n📊 Step 2: Creating health record...")
        print(f"  Heart Rate: {vital_signs['heart_rate']} bpm")
        print(f"  Blood Pressure: {vital_signs['blood_pressure_sys']}/{vital_signs['blood_pressure_dia']} mmHg")
        print(f"  SpO2: {vital_signs['spo2']}%")
        print(f"  Glucose: {vital_signs['glucose']} mg/dL")
        print(f"  BMI: {vital_signs['bmi']}")
        print(f"  Temperature: {vital_signs['temperature']}°C")
        
        # Create health record from extracted data
        health_record = HealthRecord.objects.create(
            user=request.user,
            heart_rate=vital_signs['heart_rate'],
            blood_pressure_sys=vital_signs['blood_pressure_sys'],
            blood_pressure_dia=vital_signs['blood_pressure_dia'],
            spo2=vital_signs['spo2'],
            bmi=vital_signs['bmi'],
            temperature=vital_signs['temperature'],
            glucose=vital_signs['glucose'],
            symptoms=description or 'Report analysis'
        )
        
        print(f"\n🔬 Step 3: AI analysis and predictions...")
        # Predict health risk
        result = predictor.predict(
            vital_signs['heart_rate'],
            vital_signs['blood_pressure_sys'],
            vital_signs['blood_pressure_dia'],
            vital_signs['spo2'],
            vital_signs['bmi'],
            vital_signs['temperature'],
            vital_signs['glucose']
        )
        
        # Create prediction record
        prediction = Prediction.objects.create(
            health_record=health_record,
            risk_level=result['risk_level'],
            confidence=result['confidence'],
            details=result['details'],
            specialist_needed=result['specialist_needed']
        )
        
        # Create alerts
        from health.models import Alert
        for alert_msg in result['alerts']:
            Alert.objects.create(user=request.user, prediction=prediction, message=alert_msg)
        
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  Specialist Needed: {result['specialist_needed']}")
        print(f"  Alerts: {len(result['alerts'])}")
        
        # Get doctor recommendations based on latest health data
        specialist = result['specialist_needed']
        warning_found = result['risk_level'] in ['MEDIUM', 'HIGH']
        
        print(f"\n👨‍⚕️ Step 4: Getting doctor recommendations...")
        # Get recommendations
        recs = get_recommended_doctors(request.user, report)
        print(f"  Found {len(recs)} doctor recommendations\n")
        
        # Store specialist in session for map redirect
        request.session['report_specialist'] = specialist
        request.session['report_warning'] = warning_found
        
        if warning_found:
            messages.warning(request, f'⚠️ Health report shows {result["risk_level"].lower()} risk! Found {len(recs)} doctor recommendations.')
        else:
            messages.success(request, f'✅ Report uploaded! Health data extracted. Found {len(recs)} doctor recommendations.')
        
        # If warning found, redirect to map with specialist filter
        if warning_found and specialist:
            return redirect(f"{request.build_absolute_uri('/doctors/map/')}?specialization={specialist}")
        elif warning_found:
            return redirect('doctor_map')
        else:
            return redirect('report_detail', pk=report.pk)
    
    return render(request, 'reports/upload.html')


@login_required
def report_list(request):
    reports = ReportCard.objects.filter(patient=request.user)
    return render(request, 'reports/list.html', {'reports': reports})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(ReportCard, pk=pk, patient=request.user)
    recommendations = DoctorRecommendation.objects.filter(report=report).order_by('-match_score')
    
    # Get specialist and nearby doctors
    specialist = None
    try:
        latest = HealthRecord.objects.filter(user=request.user).select_related('prediction').first()
        if latest and hasattr(latest, 'prediction'):
            specialist = latest.prediction.specialist_needed
    except Exception:
        pass
    
    # Get nearby doctors with full details
    nearby_doctors = get_nearby_doctors(request.user, specialist=specialist, radius=50)[:10]
    
    return render(request, 'reports/detail.html', {
        'report': report,
        'recommendations': recommendations,
        'specialist': specialist,
        'nearby_doctors': nearby_doctors,
    })


# ─── API Views ───────────────────────────────────────────────────────────────

class ReportUploadAPIView(generics.CreateAPIView):
    serializer_class = ReportCardSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        report = serializer.save(patient=self.request.user)
        get_recommended_doctors(self.request.user, report)


class ReportListAPIView(generics.ListAPIView):
    serializer_class = ReportCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportCard.objects.filter(patient=self.request.user)


class ReportRecommendationsAPIView(generics.ListAPIView):
    serializer_class = DoctorRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        report = get_object_or_404(ReportCard, pk=self.kwargs['pk'], patient=self.request.user)
        return DoctorRecommendation.objects.filter(report=report)
