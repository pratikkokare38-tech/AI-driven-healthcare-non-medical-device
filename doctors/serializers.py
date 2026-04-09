from rest_framework import serializers
from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Doctor
        fields = '__all__'
