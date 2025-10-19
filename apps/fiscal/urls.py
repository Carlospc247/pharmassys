from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'fiscal'

# =====================================
# Router para ViewSets da API REST
# =====================================

router = DefaultRouter()
router.register(r'taxas-iva', views.TaxaIVAAGTViewSet, basename='taxas-iva')
router.register(r'assinatura-digital', views.AssinaturaDigitalViewSet, basename='assinatura-digital')
router.register(r'retencoes-fonte', views.RetencaoFonteViewSet, basename='retencoes-fonte')

# =====================================
# URLs da API REST
# =====================================

api_urlpatterns = [
    # ViewSets registrados no router
    path('api/', include(router.urls)),
    
    # Views específicas da API
    path('api/saft/export/', views.SAFTExportView.as_view(), name='saft-export'),
    path('api/dashboard/', views.FiscalDashboardView.as_view(), name='fiscal-dashboard'),
    
    # Endpoints de validação e verificação
    path('api/validar-documento/', views.ValidarDocumentoView.as_view(), name='validar-documento'),
    path('api/verificar-integridade/', views.verificar_integridade_hash, name='verificar-integridade'),
    
    # Endpoints específicos para Taxas de IVA
    path('api/taxas-iva/ativas/', views.TaxaIVAAGTViewSet.as_view({'get': 'ativas'}), name='taxas-iva-ativas'),
    path('api/taxas-iva/<int:pk>/calcular/', views.TaxaIVAAGTViewSet.as_view({'post': 'calcular_iva'}), name='taxas-iva-calcular'),
    path('api/taxas-iva/export-saft/', views.TaxaIVAAGTViewSet.as_view({'get': 'export_saft'}), name='taxas-iva-export-saft'),
    
    # Endpoints específicos para Assinatura Digital
    path('api/assinatura/gerar-chaves/', views.AssinaturaDigitalViewSet.as_view({'post': 'gerar_chaves'}), name='assinatura-gerar-chaves'),
    path('api/assinatura/assinar-documento/', views.AssinaturaDigitalViewSet.as_view({'post': 'assinar_documento'}), name='assinatura-assinar'),
    path('api/assinatura/status-cadeia/', views.AssinaturaDigitalViewSet.as_view({'get': 'status_cadeia'}), name='assinatura-status'),
    
    # Endpoints específicos para Retenções na Fonte
    path('api/retencoes/<int:pk>/marcar-paga/', views.RetencaoFonteViewSet.as_view({'post': 'marcar_paga'}), name='retencoes-marcar-paga'),
    path('api/retencoes/relatorio-mensal/', views.RetencaoFonteViewSet.as_view({'get': 'relatorio_mensal'}), name='retencoes-relatorio-mensal'),
]

# =====================================
# URLs Web (Templates/HTML)
# =====================================

web_urlpatterns = [
    # Dashboard principal
    path('', views.FiscalDashboardTemplateView.as_view(), name='dashboard'),
    
    # Gestão de Taxas de IVA
    path('taxas-iva/', views.TaxaIVAListView.as_view(), name='taxas-iva-list'),
    path('taxas-iva/nova/', views.TaxaIVACreateView.as_view(), name='taxas-iva-create'),
    path('taxas-iva/<int:pk>/', views.TaxaIVADetailView.as_view(), name='taxas-iva-detail'),
    path('taxas-iva/<int:pk>/editar/', views.TaxaIVAUpdateView.as_view(), name='taxas-iva-update'),
    path('taxas-iva/<int:pk>/deletar/', views.TaxaIVADeleteView.as_view(), name='taxas-iva-delete'),
    
    # Gestão de Assinatura Digital
    path('assinatura/', views.AssinaturaDigitalView.as_view(), name='assinatura-digital'),
    path('assinatura/configurar/', views.AssinaturaConfigurarView.as_view(), name='assinatura-configurar'),
    path('assinatura/gerar-chaves/', views.AssinaturaGerarChavesView.as_view(), name='assinatura-gerar-chaves-web'),
    
    # Gestão de Retenções na Fonte
    path('retencoes/', views.RetencaoFonteListView.as_view(), name='retencoes-list'),
    path('retencoes/nova/', views.RetencaoFonteCreateView.as_view(), name='retencoes-create'),
    path('retencoes/<int:pk>/', views.RetencaoFonteDetailView.as_view(), name='retencoes-detail'),
    path('retencoes/<int:pk>/editar/', views.RetencaoFonteUpdateView.as_view(), name='retencoes-update'),
    path('retencoes/<int:pk>/deletar/', views.RetencaoFonteDeleteView.as_view(), name='retencoes-delete'),
    path('retencoes/<int:pk>/pagar/', views.RetencaoMarcarPagaView.as_view(), name='retencoes-pagar'),
    
    # Relatórios
    path('relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
    path('relatorios/retencoes/', views.RelatorioRetencoesView.as_view(), name='relatorio-retencoes'),
    path('relatorios/taxas-iva/', views.RelatorioTaxasIVAView.as_view(), name='relatorio-taxas-iva'),
    
    # Exportações SAF-T
    path('saft/', views.SAFTView.as_view(), name='saft'),
    path('saft/exportar/', views.SAFTExportWebView.as_view(), name='saft-export-web'),
    path('saft/historico/', views.SAFTHistoricoView.as_view(), name='saft-historico'),
    
    # Validações e Verificações
    path('validacoes/', views.ValidacoesView.as_view(), name='validacoes'),
    path('validacoes/documentos/', views.ValidarDocumentosView.as_view(), name='validar-documentos-web'),
    path('validacoes/integridade/', views.VerificarIntegridadeView.as_view(), name='verificar-integridade-web'),
    
    # Configurações Fiscais
    path('configuracoes/', views.ConfiguracoesFiscaisView.as_view(), name='configuracoes'),
    path('configuracoes/empresa/', views.ConfiguracaoEmpresaView.as_view(), name='configuracao-empresa'),
    path('configuracoes/backup/', views.BackupFiscalView.as_view(), name='backup-fiscal'),

    # Validações Fiscais
    path('validacoes/', views.ValidacoesView.as_view(), name='validacoes'),
    path('validacoes/documentos/', views.ValidarDocumentosView.as_view(), name='validar-documentos-web'),
    path('validacoes/integridade/', views.VerificarIntegridadeView.as_view(), name='verificar-integridade-web'),

    # Configurações Fiscais
    path('configuracoes/', views.ConfiguracoesFiscaisView.as_view(), name='configuracoes'),
    path('configuracoes/empresa/', views.ConfiguracaoEmpresaView.as_view(), name='configuracao-empresa'),
    path('configuracoes/backup/', views.BackupFiscalView.as_view(), name='backup-fiscal'),
]

# =====================================
# URLs de Utilitários e AJAX
# =====================================

ajax_urlpatterns = [
    # AJAX para operações rápidas
    path('ajax/calcular-iva/', views.ajax_calcular_iva, name='ajax-calcular-iva'),
    path('ajax/buscar-fornecedores/', views.ajax_buscar_fornecedores, name='ajax-buscar-fornecedores'),
    path('ajax/validar-nif/', views.ajax_validar_nif, name='ajax-validar-nif'),
    path('ajax/gerar-hash/', views.ajax_gerar_hash, name='ajax-gerar-hash'),
    
    # AJAX para relatórios dinâmicos
    path('ajax/dados-dashboard/', views.ajax_dados_dashboard, name='ajax-dados-dashboard'),
    path('ajax/metricas-periodo/', views.ajax_metricas_periodo, name='ajax-metricas-periodo'),
    path('ajax/graf-retencoes/', views.ajax_grafico_retencoes, name='ajax-grafico-retencoes'),
    
    # AJAX para validações em tempo real
    path('ajax/verificar-documento/', views.ajax_verificar_documento, name='ajax-verificar-documento'),
    path('ajax/status-assinatura/', views.ajax_status_assinatura, name='ajax-status-assinatura'),
]

# =====================================
# URLs de Downloads e Exports
# =====================================

download_urlpatterns = [
    # Downloads de relatórios
    # Downloads de relatórios
    path('download/relatorio-retencoes/<str:formato>/', views.DownloadRelatorioRetencoesView.as_view(), name='download-relatorio-retencoes'),
    path('download/relatorio-taxas/<str:formato>/', views.DownloadRelatorioTaxasView.as_view(), name='download-relatorio-taxas'),
    path('download/dashboard-pdf/', views.DownloadDashboardPDFView.as_view(), name='download-dashboard-pdf'),

    # Downloads de arquivos SAF-T
    path('download/saft/<int:export_id>/', views.DownloadSAFTFileView.as_view(), name='download-saft-file'),
    path('download/saft-backup/', views.DownloadSAFTBackupView.as_view(), name='download-saft-backup'),

    # Downloads de templates e exemplos
    path('download/template-retencoes/', views.DownloadTemplateRetencoesView.as_view(), name='download-template-retencoes'),
    path('download/exemplo-saft/', views.DownloadExemploSAFTView.as_view(), name='download-exemplo-saft'),

    # Download de chave pública
    path('download/chave-publica/', views.DownloadChavePublicaView.as_view(), name='download-chave-publica'),
]

# =====================================
# URLs de Webhooks e Integrações
# =====================================

webhook_urlpatterns = [
    # Webhooks para integrações externas
    path('webhook/agt-notification/', views.webhook_agt_notification, name='webhook-agt'),   
    # APIs para integrações de terceiros
    path('integracoes/agt/validar/', views.integracao_agt_validar, name='integracao-agt-validar'),
    path('integracoes/saft/submit/', views.integracao_saft_submit, name='integracao-saft-submit'),
]

# =====================================
# URLs Combinadas
# =====================================

urlpatterns = [
    # URLs da API REST
    *api_urlpatterns,
    
    # URLs Web (Templates)
    *web_urlpatterns,
    
    # URLs AJAX
    *ajax_urlpatterns,
    
    # URLs de Downloads
    *download_urlpatterns,
    
    # URLs de Webhooks (opcional)
    *webhook_urlpatterns,
]

# =====================================
# URLs de Desenvolvimento/Debug
# =====================================

# Incluir apenas em modo DEBUG
from django.conf import settings

if settings.DEBUG:
    debug_urlpatterns = [
        # URLs para testes e desenvolvimento
        path('debug/gerar-dados-teste/', views.debug_gerar_dados_teste, name='debug-gerar-dados'),
        path('debug/limpar-cache/', views.debug_limpar_cache, name='debug-limpar-cache'),
        path('debug/info-sistema/', views.debug_info_sistema, name='debug-info-sistema'),
        path('debug/testar-assinatura/', views.debug_testar_assinatura, name='debug-testar-assinatura'),
        path('debug/simular-agt/', views.debug_simular_agt, name='debug-simular-agt'),
    ]
    
    urlpatterns += debug_urlpatterns

# =====================================
# Documentação das URLs
# =====================================

"""
Documentação das URLs do app Fiscais:

=== API REST ===
GET    /fiscais/api/taxas-iva/                    - Lista taxas de IVA
POST   /fiscais/api/taxas-iva/                    - Cria nova taxa de IVA
GET    /fiscais/api/taxas-iva/{id}/               - Detalhes de uma taxa
PUT    /fiscais/api/taxas-iva/{id}/               - Atualiza taxa
DELETE /fiscais/api/taxas-iva/{id}/               - Remove taxa
GET    /fiscais/api/taxas-iva/ativas/             - Lista apenas taxas ativas
POST   /fiscais/api/taxas-iva/{id}/calcular/      - Calcula IVA para valor
GET    /fiscais/api/taxas-iva/export-saft/        - Exporta taxas em formato SAF-T

GET    /fiscais/api/assinatura-digital/           - Info da assinatura digital
POST   /fiscais/api/assinatura/gerar-chaves/      - Gera novas chaves RSA
POST   /fiscais/api/assinatura/assinar-documento/ - Assina um documento
GET    /fiscais/api/assinatura/status-cadeia/     - Status da cadeia de integridade

GET    /fiscais/api/retencoes-fonte/              - Lista retenções na fonte
POST   /fiscais/api/retencoes-fonte/              - Cria nova retenção
GET    /fiscais/api/retencoes-fonte/{id}/         - Detalhes de uma retenção
PUT    /fiscais/api/retencoes-fonte/{id}/         - Atualiza retenção
DELETE /fiscais/api/retencoes-fonte/{id}/         - Remove retenção
POST   /fiscais/api/retencoes/{id}/marcar-paga/   - Marca retenção como paga
GET    /fiscais/api/retencoes/relatorio-mensal/   - Relatório mensal de retenções

POST   /fiscais/api/saft/export/                  - Exporta arquivo SAF-T AO completo
GET    /fiscais/api/dashboard/                    - Dados do dashboard fiscal
POST   /fiscais/api/validar-documento/            - Valida documento fiscal
GET    /fiscais/api/verificar-integridade/        - Verifica integridade da cadeia

=== URLs Web ===
GET    /fiscais/                                  - Dashboard principal
GET    /fiscais/taxas-iva/                        - Lista taxas de IVA (web)
GET    /fiscais/retencoes/                        - Lista retenções (web)
GET    /fiscais/saft/                             - Interface SAF-T
GET    /fiscais/relatorios/                       - Relatórios fiscais
GET    /fiscais/configuracoes/                    - Configurações fiscais

=== Downloads ===
GET    /fiscais/download/relatorio-retencoes/pdf/ - Download relatório PDF
GET    /fiscais/download/saft/{id}/               - Download arquivo SAF-T
GET    /fiscais/download/chave-publica/           - Download chave pública

=== AJAX ===
POST   /fiscais/ajax/calcular-iva/                - Cálculo IVA via AJAX
GET    /fiscais/ajax/dados-dashboard/             - Dados dashboard via AJAX
POST   /fiscais/ajax/verificar-documento/         - Verificação documento via AJAX

=== Webhooks ===
POST   /fiscais/webhook/agt-notification/         - Webhook notificações AGT
POST   /fiscais/integracoes/agt/validar/          - Integração validação AGT

Todas as URLs requerem autenticação exceto webhooks.
URLs da API retornam JSON, URLs web retornam HTML.
"""