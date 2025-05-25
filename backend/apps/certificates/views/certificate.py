from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.certificates.models import Certificate
from apps.certificates.serializers import CertificateSerializer


class CertificateViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Certificate.objects.all().select_related('issued_to', 'issued_by', 'csr')

        # Пример, если в модели User есть поле role
        if hasattr(user, 'role'):
            if user.role == 'employee':
                return qs.filter(issued_to=user)
            elif user.role in ['admin', 'manager']:
                return qs
            else:
                # Можно ограничить для других ролей, если есть
                return qs.none()
        else:
            # Если нет поля role, fallback к суперпользователю
            if user.is_superuser or user.groups.filter(name="Руководитель").exists():
                return qs
            return qs.filter(issued_to=user)


    @extend_schema(
        summary="Проверка валидности сертификата",
        description="Проверяет, действителен ли сертификат (не отозван и не истёк).",
        responses={
            200: inline_serializer(
                name="ValidationResponse",
                fields={
                    "valid": serializers.BooleanField(),
                    "reason": serializers.CharField(),
                    "revoked_at": serializers.DateTimeField(required=False),
                    "expired_at": serializers.DateTimeField(required=False),
                }
            )
        }
    )
    @action(detail=True, methods=["get"])
    def validate(self, request, pk=None):
        cert = self.get_object()
        now = timezone.now()

        if cert.revoked:
            return Response({"valid": False, "reason": "revoked", "revoked_at": cert.revoked_at})

        if cert.expires_at < now:
            return Response({"valid": False, "reason": "expired", "expired_at": cert.expires_at})

        return Response({"valid": True, "reason": "active"})
