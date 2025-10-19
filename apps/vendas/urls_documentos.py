# apps/vendas/urls_documentos.py

from django.urls import path
from . import views

app_name = 'vendas_documentos'

urlpatterns = [
    # =====================================
    # NOTAS DE CRÉDITO
    # =====================================
    path('notas-credito/', views.NotaCreditoListView.as_view(), name='nota_credito_lista'),
    path('notas-credito/nova/', views.NotaCreditoCreateView.as_view(), name='nota_credito_create'),
    path('notas-credito/<int:pk>/', views.NotaCreditoDetailView.as_view(), name='nota_credito_detail'),
    path('notas-credito/<int:pk>/editar/', views.NotaCreditoUpdateView.as_view(), name='nota_credito_update'),
    path('notas-credito/<int:pk>/aplicar/', views.AplicarNotaCreditoView.as_view(), name='aplicar_nota_credito'),
    path('notas-credito/<int:pk>/aprovar/', views.AprovarNotaCreditoView.as_view(), name='aprovar_nota_credito'),
    path('notas-credito/<int:nota_id>/pdf/', views.nota_credito_pdf_view, name='nota_credito_pdf'),
    
    # =====================================
    # NOTAS DE DÉBITO
    # =====================================
    path('notas-debito/', views.NotaDebitoListView.as_view(), name='nota_debito_lista'),
    path('notas-debito/nova/', views.NotaDebitoCreateView.as_view(), name='nota_debito_create'),
    path('notas-debito/<int:pk>/', views.NotaDebitoDetailView.as_view(), name='nota_debito_detail'),
    path('notas-debito/<int:pk>/editar/', views.NotaDebitoUpdateView.as_view(), name='nota_debito_update'),
    path('notas-debito/<int:pk>/aplicar/', views.AplicarNotaDebitoView.as_view(), name='aplicar_nota_debito'),
    path('notas-debito/<int:pk>/aprovar/', views.AprovarNotaDebitoView.as_view(), name='aprovar_nota_debito'),
    path('notas-debito/<int:nota_id>/pdf/', views.nota_debito_pdf_view, name='nota_debito_pdf'),
    
    # =====================================
    # DOCUMENTOS DE TRANSPORTE
    # =====================================
    path('documentos-transporte/', views.DocumentoTransporteListView.as_view(), name='documento_transporte_lista'),
    path('documentos-transporte/novo/', views.DocumentoTransporteCreateView.as_view(), name='documento_transporte_create'),
    path('documentos-transporte/<int:pk>/', views.DocumentoTransporteDetailView.as_view(), name='documento_transporte_detail'),
    path('documentos-transporte/<int:pk>/editar/', views.DocumentoTransporteUpdateView.as_view(), name='documento_transporte_update'),
    path('documentos-transporte/<int:pk>/iniciar/', views.IniciarTransporteView.as_view(), name='iniciar_transporte'),
    path('documentos-transporte/<int:pk>/confirmar-entrega/', views.ConfirmarEntregaView.as_view(), name='confirmar_entrega'),
    path('documentos-transporte/<int:documento_id>/pdf/', views.documento_transporte_pdf_view, name='documento_transporte_pdf'),
    
    # =====================================
    # DASHBOARDS E RELATÓRIOS
    # =====================================
    path('analytics/documentos-fiscais/', views.DocumentosFiscaisAnalyticsView.as_view(), name='documentos_fiscais_analytics'),
    path('relatorios/notas-credito/', views.RelatorioNotasCreditoView.as_view(), name='relatorio_notas_credito'),
    path('relatorios/transportes/', views.RelatorioTransportesView.as_view(), name='relatorio_transportes'),
    
    # =====================================
    # APIs
    # =====================================
    path('api/finalizar-nota-credito/', views.finalizar_nota_credito_api, name='finalizar_nota_credito_api'),
    path('api/finalizar-nota-debito/', views.finalizar_nota_debito_api, name='finalizar_nota_debito_api'),
    path('api/finalizar-documento-transporte/', views.finalizar_documento_transporte_api, name='finalizar_documento_transporte_api'),
    path('api/buscar-documentos-origem/', views.buscar_documentos_origem_api, name='buscar_documentos_origem_api'),

    # Adicionar no final do arquivo apps/vendas/urls_documentos.py:

    # APIs para gestão de itens
    path('api/adicionar-item-nc/', views.adicionar_item_nota_credito_api, name='adicionar_item_nota_credito_api'),
    path('api/adicionar-item-nd/', views.adicionar_item_nota_debito_api, name='adicionar_item_nota_debito_api'),
    path('api/adicionar-item-gt/', views.adicionar_item_documento_transporte_api, name='adicionar_item_documento_transporte_api'),
    path('api/remover-item-nc/<int:item_id>/', views.remover_item_nota_credito_api, name='remover_item_nota_credito_api'),
    path('api/remover-item-nd/<int:item_id>/', views.remover_item_nota_debito_api, name='remover_item_nota_debito_api'),
    path('api/remover-item-gt/<int:item_id>/', views.remover_item_documento_transporte_api, name='remover_item_documento_transporte_api'),
    
    # APIs de busca
    path('api/buscar-produtos/', views.buscar_produtos_api, name='buscar_produtos_api'),
    path('api/buscar-servicos/', views.buscar_servicos_api, name='buscar_servicos_api'),
    path('api/buscar-clientes/', views.buscar_clientes_api, name='buscar_clientes_api'),
    path('api/estatisticas-rapidas/', views.estatisticas_rapidas_api, name='estatisticas_rapidas_api'),
]