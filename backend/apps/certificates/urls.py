from django.urls import path, include
from rest_framework.routers import DefaultRouter

import apps.certificates.views.certificate
import apps.certificates.views.revocation
from .views import CRLView, OCSPResponderView, SignFileView, VerifySignatureView

router = DefaultRouter()

router.register(r'certificate-requests', apps.certificates.views.certificate_request.CertificateRequestViewSet, basename='certificate-requests')
router.register(r'certificates', apps.certificates.views.certificate.CertificateViewSet, basename='certificate')
router.register(r'revocations', apps.certificates.views.revocation.RevocationViewSet, basename='revocation')


urlpatterns = [
    path('', include(router.urls)),
    path("crl/", CRLView.as_view(), name="crl"),
    path("ocsp/", OCSPResponderView.as_view(), name="ocsp"),
    path('sign-file/', SignFileView.as_view(), name="sign-file"),
    path('verify-file/', VerifySignatureView.as_view(), name="verify-file"),

]
