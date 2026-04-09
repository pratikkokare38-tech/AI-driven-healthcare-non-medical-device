from django.contrib import admin
from .models import ReportCard, DoctorRecommendation


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['patient', 'title', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['patient__username', 'title', 'description']


@admin.register(DoctorRecommendation)
class DoctorRecommendationAdmin(admin.ModelAdmin):
    list_display = ['report', 'doctor', 'match_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['report__patient__username', 'doctor__name']
