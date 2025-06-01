from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.certificates.models import CertificateRequest, Authority
from apps.certificates.serializers import CertificateRequestSerializer
from services.ca import sign_csr


class CertificateRequestViewSet(viewsets.ModelViewSet):
    queryset = CertificateRequest.objects.all().order_by('-created_at')
    serializer_class = CertificateRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'status']

    def perform_create(self, serializer):
        # При создании CSR автоматически привязываем к текущему пользователю
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        # Админ и руководитель видят все заявки
        if user.is_superuser or user.groups.filter(name="Руководитель").exists():
            return CertificateRequest.objects.all()
        # Обычные пользователи видят только свои заявки
        return CertificateRequest.objects.filter(user=user)

    @swagger_auto_schema(
        method="post",
        operation_summary="Одобрить CSR-заявку",
        operation_description="Одобрить CSR-заявку",
        responses={
            200: openapi.Response("Заявка одобрена", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: "Заявка уже обработана"
        }
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        csr = self.get_object()

        if csr.status != "pending":
            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_400_BAD_REQUEST)
        csr.status = "approved"
        csr.save()
        # Здесь можно добавить логику выпуска сертификата по CSR
        return Response({"detail": "Заявка одобрена."})

    @swagger_auto_schema(
        method='post',
        operation_summary="Отклонить заявку.",
        operation_description="Отклонить заявку на сертификат.",
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        csr = self.get_object()
        if csr.status != "pending":
            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_400_BAD_REQUEST)
        csr.status = "rejected"
        csr.save()
        return Response({"detail": "Заявка отклонена."})

    @swagger_auto_schema(
        method='post',
        operation_summary="Подписать CSR",
        operation_description="Подписывает одобренный запрос на сертификат через подчинённый УЦ (в зависимости от группы пользователя).",
        responses={
            200: openapi.Response(description="Сертификат успешно подписан"),
            400: "CSR is not approved.",
            404: "Appropriate intermediate CA not found.",
            500: "Signing error"
        }
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def sign(self, request, pk=None):
        csr_obj = self.get_object()

        if csr_obj.status != "approved":
            return Response({"detail": "CSR is not approved."}, status=status.HTTP_400_BAD_REQUEST)

        # Определяем нужный подчинённый УЦ (например, "users")

        try:
            purpose = "services" if csr_obj.user.groups.filter(name="Сервисы").exists() else "users"
            ca = Authority.objects.get(purpose=purpose, is_root=False)
        except Authority.DoesNotExist:
            return Response({"detail": "Appropriate intermediate CA not found."}, status=404)

        # Подписываем
        try:
            certificate = sign_csr(csr_obj.csr_pem, ca, csr_obj.user)
            certificate.csr = csr_obj
            certificate.save()
            csr_obj.status = "signed"
        except Exception as e:
            return Response({"detail": f"Signing error: {e}"}, status=500)
        return Response({"detail": "Certificate signed successfully.", "cert_id": certificate.id})

    @swagger_auto_schema()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)



