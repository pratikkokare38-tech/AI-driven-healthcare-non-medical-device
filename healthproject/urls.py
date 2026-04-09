from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Web views
    path('', include('accounts.urls')),
    path('dashboard/', include('health.urls')),
    path('doctors/', include('doctors.urls')),
    path('reports/', include('reports.urls')),
    # DRF API
    path('api/auth/', include('accounts.api_urls')),
    path('api/health/', include('health.api_urls')),
    path('api/doctors/', include('doctors.api_urls')),
    path('api/reports/', include('reports.api_urls')),
    # JWT
    path('api/token/', __import__('rest_framework_simplejwt.views', fromlist=['TokenObtainPairView']).TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', __import__('rest_framework_simplejwt.views', fromlist=['TokenRefreshView']).TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
