from django.urls import path
from . import api_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('login/', TokenObtainPairView.as_view(), name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),
]
