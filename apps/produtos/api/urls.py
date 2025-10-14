# apps/produtos/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'produtos'

router = DefaultRouter()
# router.register(r'exemplo', viewsets.ExemploViewSet, basename='exemplo')

urlpatterns = [
    path('api/', include(router.urls)),
]
