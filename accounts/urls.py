from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.landing_page, name='landing'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Phone Verification
    path('auth/verify-phone/<int:user_id>/', views.verify_phone_view, name='verify_phone'),
    path('auth/resend-otp/<int:user_id>/', views.resend_otp_view, name='resend_otp'),
    
    # Password Reset
    path('auth/forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('auth/reset-password/<int:user_id>/', views.reset_password_view, name='reset_password'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
]
