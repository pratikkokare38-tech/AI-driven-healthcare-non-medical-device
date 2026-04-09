import math
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import HealthRecord, Prediction, Alert
from .serializers import HealthRecordSerializer, PredictionSerializer, AlertSerializer, HealthInputSerializer
from .ml_model import predictor


# ─── Web Views ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Display health dashboard with trends and analysis"""
    records = HealthRecord.objects.filter(user=request.user)[:10]
    alerts = Alert.objects.filter(user=request.user, is_read=False)[:5]
    unread_count = Alert.objects.filter(user=request.user, is_read=False).count()
    latest = records.first()
    
    # Chart data - last 20 records for trend analysis (ascending for time-series chart)
    # We want the newest 20 records, but displayed chronologically
    recent_records = HealthRecord.objects.filter(user=request.user).order_by('-timestamp')[:20]
    raw_chart = list(recent_records.values(
        'timestamp', 'heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'spo2', 'glucose'
    ))
    # Reverse to make it chronological (left to right)
    raw_chart.reverse()
    
    # Convert datetime objects → ISO strings so template JSON is valid
    chart_rows = []
    for row in raw_chart:
        chart_rows.append({
            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else '',
            'heart_rate': float(row['heart_rate'] or 0),
            'blood_pressure_sys': float(row['blood_pressure_sys'] or 0),
            'blood_pressure_dia': float(row['blood_pressure_dia'] or 0),
            'spo2': float(row['spo2'] or 0),
            'glucose': float(row['glucose'] or 0),
        })
    chart_data = json.dumps(chart_rows)
    
    # Calculate health score based on latest metrics
    health_score = 100
    if latest:
        # Heart rate: ideal 60-100 bpm
        if not (60 <= latest.heart_rate <= 100):
            health_score -= abs(latest.heart_rate - 80) / 20
        
        # Blood pressure: ideal < 120/80
        if latest.blood_pressure_sys > 140 or latest.blood_pressure_dia > 90:
            health_score -= 15
        elif latest.blood_pressure_sys > 120 or latest.blood_pressure_dia > 80:
            health_score -= 5
        
        # SpO2: ideal > 95%
        if latest.spo2 < 95:
            health_score -= (95 - latest.spo2) * 2
        
        # Glucose: ideal 70-100 fasting
        if latest.glucose < 70 or latest.glucose > 130:
            health_score -= 10
        
        health_score = max(0, min(100, int(health_score)))
    else:
        health_score = None
    
    return render(request, 'health/dashboard.html', {
        'records': records,
        'alerts': alerts,
        'unread_count': unread_count,
        'latest': latest,
        'chart_data': chart_data,
        'health_score': health_score,
    })


@login_required
def health_input(request):
    if request.method == 'POST':
        try:
            hr = float(request.POST['heart_rate'])
            sbp = float(request.POST['blood_pressure_sys'])
            dbp = float(request.POST['blood_pressure_dia'])
            spo2 = float(request.POST['spo2'])
            bmi = float(request.POST['bmi'])
            temp = float(request.POST['temperature'])
            glucose = float(request.POST['glucose'])
            symptoms = request.POST.get('symptoms', '')

            record = HealthRecord.objects.create(
                user=request.user, heart_rate=hr, blood_pressure_sys=sbp,
                blood_pressure_dia=dbp, spo2=spo2, bmi=bmi,
                temperature=temp, glucose=glucose, symptoms=symptoms
            )
            result = predictor.predict(hr, sbp, dbp, spo2, bmi, temp, glucose)
            prediction = Prediction.objects.create(
                health_record=record,
                risk_level=result['risk_level'],
                confidence=result['confidence'],
                details=result['details'],
                specialist_needed=result['specialist_needed']
            )
            for alert_msg in result['alerts']:
                Alert.objects.create(user=request.user, prediction=prediction, message=alert_msg)

            messages.success(request, 'Health data submitted and analyzed!')
            return redirect('prediction_result', pk=prediction.pk)
        except (KeyError, ValueError) as e:
            messages.error(request, f'Invalid input: {str(e)}')
    return render(request, 'health/input.html')


@login_required
def prediction_result(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, health_record__user=request.user)
    alerts = Alert.objects.filter(prediction=prediction)
    return render(request, 'health/result.html', {
        'prediction': prediction,
        'record': prediction.health_record,
        'alerts': alerts,
    })


@login_required
def health_history(request):
    records = HealthRecord.objects.filter(user=request.user)
    return render(request, 'health/history.html', {'records': records})


@login_required
def alerts_view(request):
    Alert.objects.filter(user=request.user, is_read=False).update(is_read=True)
    alerts = Alert.objects.filter(user=request.user)
    return render(request, 'health/alerts.html', {'alerts': alerts})


# ─── API Views ───────────────────────────────────────────────────────────────

class HealthRecordListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HealthRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HealthRecordDetailAPIView(generics.RetrieveAPIView):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HealthRecord.objects.filter(user=self.request.user)


class PredictAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = HealthInputSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        d = ser.validated_data
        record = HealthRecord.objects.create(user=request.user, **d)
        result = predictor.predict(
            d['heart_rate'], d['blood_pressure_sys'], d['blood_pressure_dia'],
            d['spo2'], d['bmi'], d['temperature'], d['glucose']
        )
        prediction = Prediction.objects.create(
            health_record=record,
            risk_level=result['risk_level'],
            confidence=result['confidence'],
            details=result['details'],
            specialist_needed=result['specialist_needed']
        )
        for alert_msg in result['alerts']:
            Alert.objects.create(user=request.user, prediction=prediction, message=alert_msg)
        return Response({
            'record': HealthRecordSerializer(record).data,
            'prediction': PredictionSerializer(prediction).data,
            'alerts': result['alerts'],
        }, status=status.HTTP_201_CREATED)


class AlertListAPIView(generics.ListAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)


class AlertMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk, user=request.user)
        alert.is_read = True
        alert.save()
        return Response({'status': 'marked as read'})
