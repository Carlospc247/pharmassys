# apps/saft/urls.py

from django.urls import path
from .views import SaftExportView

urlpatterns = [
    # /saft/exportar/
    path('exportar/', SaftExportView.as_view(), name='saft_export'),
]