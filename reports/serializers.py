from rest_framework import serializers
from .models import ReportCard, DoctorRecommendation
from doctors.serializers import DoctorSerializer


class ReportCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCard
        fields = '__all__'
        read_only_fields = ['patient', 'uploaded_at', 'file_type']


class DoctorRecommendationSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = DoctorRecommendation
        fields = '__all__'
