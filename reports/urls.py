from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('upload/', views.report_upload, name='report_upload'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
]
