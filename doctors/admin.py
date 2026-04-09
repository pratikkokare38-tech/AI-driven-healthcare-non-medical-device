from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'hospital_name', 'city', 'rating', 'consultation_fee', 'is_available']
    list_filter = ['specialization', 'is_available', 'city']
    search_fields = ['name', 'hospital_name', 'city', 'license_number']
    list_editable = ['is_available', 'rating']
