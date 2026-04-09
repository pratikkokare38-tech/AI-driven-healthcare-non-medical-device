from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.ReportUploadAPIView.as_view(), name='api_report_upload'),
    path('', views.ReportListAPIView.as_view(), name='api_report_list'),
    path('<int:pk>/recommendations/', views.ReportRecommendationsAPIView.as_view(), name='api_report_recommendations'),
]
