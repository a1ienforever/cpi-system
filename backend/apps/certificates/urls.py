from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'certificate-requests', views.CertificateRequestViewSet, basename='certificate-requests')
router.register(r'certificates', views.CertificateViewSet, basename='certificate')



urlpatterns = [
    path('', include(router.urls)),
    ]
