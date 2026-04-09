from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.HealthRecordListCreateAPIView.as_view(), name='api_health_records'),
    path('records/<int:pk>/', views.HealthRecordDetailAPIView.as_view(), name='api_health_detail'),
    path('predict/', views.PredictAPIView.as_view(), name='api_predict'),
    path('alerts/', views.AlertListAPIView.as_view(), name='api_alerts'),
    path('alerts/<int:pk>/read/', views.AlertMarkReadAPIView.as_view(), name='api_alert_read'),
]
