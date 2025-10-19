
# apps/saft/urls.py (URLs completas)

from django.urls import path
from . import views

app_name = 'saft'

urlpatterns = [
    # Exportação principal
    path('export/', views.SaftExportView.as_view(), name='saft_export'),
    
    # Histórico e gestão
    path('historico/', views.SaftHistoricoView.as_view(), name='historico'),
    path('download/<int:export_id>/', views.SaftDownloadView.as_view(), name='download'),
    path('visualizar/<int:export_id>/', views.SaftVisualizarView.as_view(), name='visualizar'),
    
    # Validação
    path('validar/', views.SaftValidarView.as_view(), name='validar'),
    
    # AJAX endpoints
    path('ajax/status/', views.SaftStatusAjaxView.as_view(), name='ajax-status'),
]
    