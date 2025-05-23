from django.urls import path
from . import views

urlpatterns = [
    # примеры маршрутов
    path('', views.index, name='certificates_index'),
]
