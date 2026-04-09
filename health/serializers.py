from rest_framework import serializers
from .models import HealthRecord, Prediction, Alert


class HealthRecordSerializer(serializers.ModelSerializer):
    prediction = serializers.SerializerMethodField()

    class Meta:
        model = HealthRecord
        fields = '__all__'
        read_only_fields = ['user', 'timestamp']

    def get_prediction(self, obj):
        if hasattr(obj, 'prediction'):
            return PredictionSerializer(obj.prediction).data
        return None


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'
        read_only_fields = ['health_record', 'created_at']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['user', 'prediction', 'created_at']


class HealthInputSerializer(serializers.Serializer):
    heart_rate = serializers.FloatField(min_value=20, max_value=300)
    blood_pressure_sys = serializers.FloatField(min_value=50, max_value=300)
    blood_pressure_dia = serializers.FloatField(min_value=30, max_value=200)
    spo2 = serializers.FloatField(min_value=50, max_value=100)
    bmi = serializers.FloatField(min_value=10, max_value=70)
    temperature = serializers.FloatField(min_value=30, max_value=45)
    glucose = serializers.FloatField(min_value=20, max_value=600)
    symptoms = serializers.CharField(required=False, allow_blank=True, default='')
