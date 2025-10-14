# apps/financeiro/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'financeiro'

router = DefaultRouter()
# router.register(r'exemplo', viewsets.ExemploViewSet, basename='exemplo')

urlpatterns = [
    path('api/', include(router.urls)),
]
