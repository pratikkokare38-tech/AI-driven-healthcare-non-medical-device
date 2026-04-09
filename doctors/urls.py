from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('map/', views.doctor_map, name='doctor_map'),
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
]
