from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import CertificateRequest, Certificate
from .serializers import CertificateRequestSerializer, CertificateSerializer


class CertificateRequestViewSet(viewsets.ModelViewSet):
    queryset = CertificateRequest.objects.all().order_by('-created_at')
    serializer_class = CertificateRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

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

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        csr = self.get_object()
        if csr.status != "pending":
            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_400_BAD_REQUEST)
        csr.status = "approved"
        csr.save()
        # Здесь можно добавить логику выпуска сертификата по CSR
        return Response({"detail": "Заявка одобрена."})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        csr = self.get_object()
        if csr.status != "pending":
            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_400_BAD_REQUEST)
        csr.status = "rejected"
        csr.save()
        return Response({"detail": "Заявка отклонена."})


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
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
