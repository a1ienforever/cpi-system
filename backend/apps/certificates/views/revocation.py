from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, serializers
from rest_framework.mixins import CreateModelMixin

from apps.certificates.models import Revocation
from apps.certificates.serializers import RevocationSerializer


class RevocationViewSet(CreateModelMixin ,viewsets.GenericViewSet):
    queryset = Revocation.objects.all()
    serializer_class = RevocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Отозвать сертификат",
        operation_description="Создаёт запись об отзыве сертификата и помечает сертификат как отозванный.",
        responses={
            201: RevocationSerializer,
            400: "Сертификат уже отозван или неверный запрос",
            401: "Требуется аутентификация",
        }
    )
    def perform_create(self, serializer):
        cert = serializer.validated_data["certificate"]

        if cert.revoked:
            raise serializers.ValidationError("Certificate already revoked.")

        cert.revoked = True
        cert.revoked_at = timezone.now()
        cert.save()

        serializer.save(revoked_at=cert.revoked_at)
