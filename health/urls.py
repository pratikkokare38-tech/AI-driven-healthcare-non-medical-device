from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('health/input/', views.health_input, name='health_input'),
    path('health/result/<int:pk>/', views.prediction_result, name='prediction_result'),
    path('health/history/', views.health_history, name='health_history'),
    path('health/alerts/', views.alerts_view, name='alerts'),
]
