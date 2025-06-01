from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User
from apps.users.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email']
    ordering_fields = ['email']

    @action(methods=['get'], detail=False)
    def about_me(self, request):
        user = request.user
        return Response({
            'email': user.email,
            'is_admin': user.is_superuser,
        })