from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.users.views import UserViewSet

router = DefaultRouter()

router.register('users', UserViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),    # Получить access и refresh токены
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),         # Обновить access по refresh токену
]
