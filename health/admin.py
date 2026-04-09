from django.contrib import admin
from .models import HealthRecord, Prediction, Alert


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'spo2', 'bmi', 'temperature', 'glucose', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'symptoms']
    date_hierarchy = 'timestamp'


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['health_record', 'risk_level', 'confidence', 'specialist_needed', 'created_at']
    list_filter = ['risk_level', 'created_at']
    search_fields = ['health_record__user__username']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']
