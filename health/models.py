from django.db import models
from django.conf import settings


class HealthRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='health_records')
    heart_rate = models.FloatField(help_text="Beats per minute (BPM)")
    blood_pressure_sys = models.FloatField(help_text="Systolic BP (mmHg)")
    blood_pressure_dia = models.FloatField(help_text="Diastolic BP (mmHg)")
    spo2 = models.FloatField(help_text="Oxygen Saturation (%)")
    bmi = models.FloatField(help_text="Body Mass Index")
    temperature = models.FloatField(help_text="Body Temperature (°C)")
    glucose = models.FloatField(help_text="Blood Glucose (mg/dL)")
    symptoms = models.TextField(blank=True, help_text="Describe any symptoms")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Prediction(models.Model):
    RISK_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]
    health_record = models.OneToOneField(HealthRecord, on_delete=models.CASCADE, related_name='prediction')
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    confidence = models.FloatField(default=0.0)
    details = models.TextField()
    specialist_needed = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.health_record.user.username} - {self.risk_level} ({self.confidence:.0f}%)"

    def get_risk_color(self):
        return {'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger'}.get(self.risk_level, 'secondary')

    def get_risk_icon(self):
        return {'LOW': '✅', 'MEDIUM': '⚠️', 'HIGH': '🚨'}.get(self.risk_level, '❓')


class Alert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert for {self.user.username} - {'Read' if self.is_read else 'Unread'}"
