from django.urls import path
from . import views

urlpatterns = [
    path('', views.DoctorListAPIView.as_view(), name='api_doctor_list'),
    path('<int:pk>/', views.DoctorDetailAPIView.as_view(), name='api_doctor_detail'),
    path('nearby/', views.NearbyDoctorsAPIView.as_view(), name='api_nearby_doctors'),
    path('save-location/', views.SaveUserLocationAPIView.as_view(), name='api_save_user_location'),
]
