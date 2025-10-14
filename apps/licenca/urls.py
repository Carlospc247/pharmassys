# apps/licencas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import viewsets

# API Router
router = DefaultRouter()
router.register(r'licencas', viewsets.LicencaViewSet)
router.register(r'renovacoes', viewsets.RenovacaoViewSet)
router.register(r'documentos', viewsets.DocumentoLicencaViewSet)

app_name = 'licencas'

urlpatterns = [
    # =====================================
    # DASHBOARD E LISTAGENS
    # =====================================
    path('', views.LicencaDashboardView.as_view(), name='dashboard'),
    path('lista/', views.LicencaListView.as_view(), name='lista'),
    path('vencimentos/', views.VencimentosView.as_view(), name='vencimentos'),
    
    # =====================================
    # GESTÃO DE LICENÇAS
    # =====================================
    path('nova/', views.LicencaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.LicencaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.LicencaUpdateView.as_view(), name='update'),
    path('<int:pk>/deletar/', views.LicencaDeleteView.as_view(), name='delete'),
    
    # =====================================
    # RENOVAÇÕES
    # =====================================
    path('<int:pk>/renovar/', views.RenovarLicencaView.as_view(), name='renovar'),
    path('renovacoes/', views.RenovacaoListView.as_view(), name='renovacao_lista'),
    path('renovacoes/<int:pk>/', views.RenovacaoDetailView.as_view(), name='renovacao_detail'),
    path('renovacoes/<int:pk>/finalizar/', views.FinalizarRenovacaoView.as_view(), name='renovacao_finalizar'),
    
    # =====================================
    # DOCUMENTOS
    # =====================================
    path('<int:licenca_pk>/documentos/', views.DocumentoListView.as_view(), name='documento_lista'),
    path('<int:licenca_pk>/documentos/novo/', views.DocumentoCreateView.as_view(), name='documento_create'),
    path('documentos/<int:pk>/', views.DocumentoDetailView.as_view(), name='documento_detail'),
    path('documentos/<int:pk>/download/', views.DocumentoDownloadView.as_view(), name='documento_download'),
    
    # =====================================
    # TIPOS ESPECÍFICOS DE LICENÇAS
    # =====================================
    # Licenças Farmacêuticas
    path('farmaceuticas/', views.LicencasFarmaceuticasView.as_view(), name='farmaceuticas'),
    path('funcionamento/', views.LicencaFuncionamentoView.as_view(), name='funcionamento'),
    path('sanitaria/', views.LicencaSanitariaView.as_view(), name='sanitaria'),
    
    # ANVISA
    path('anvisa/', views.LicencasAnvisaView.as_view(), name='anvisa'),
    path('afvs/', views.AFVSView.as_view(), name='afvs'),
    path('aie/', views.AIEView.as_view(), name='aie'),
    
    # OFA
    path('ofa/', views.LicencasOFAView.as_view(), name='ofa'),
    path('responsavel-tecnico/', views.ResponsavelTecnicoView.as_view(), name='responsavel_tecnico'),
    
    # Vigilância Sanitária
    path('vigilancia/', views.VigilanciaSanitariaView.as_view(), name='vigilancia'),
    path('estadual/', views.LicencaEstadualView.as_view(), name='estadual'),
    path('municipal/', views.LicencaMunicipalView.as_view(), name='municipal'),
    
    # =====================================
    # PROCESSOS E PROTOCOLOS
    # =====================================
    path('processos/', views.ProcessoListView.as_view(), name='processo_lista'),
    path('processos/novo/', views.ProcessoCreateView.as_view(), name='processo_create'),
    path('processos/<int:pk>/', views.ProcessoDetailView.as_view(), name='processo_detail'),
    path('processos/<int:pk>/acompanhar/', views.AcompanharProcessoView.as_view(), name='processo_acompanhar'),
    
    # =====================================
    # ALERTAS E NOTIFICAÇÕES
    # =====================================
    path('alertas/', views.AlertasView.as_view(), name='alertas'),
    path('configurar-alertas/', views.ConfigurarAlertasView.as_view(), name='configurar_alertas'),
    path('notificacoes/', views.NotificacoesView.as_view(), name='notificacoes'),
    
    # =====================================
    # CALENDÁRIO REGULATÓRIO
    # =====================================
    path('calendario/', views.CalendarioRegulatorioreView.as_view(), name='calendario'),
    path('cronograma/', views.CronogramaRenovacoesView.as_view(), name='cronograma'),
    path('agenda/', views.AgendaComplianceView.as_view(), name='agenda'),
    
    # =====================================
    # RELATÓRIOS E COMPLIANCE
    # =====================================
    path('relatorios/', views.LicencaRelatoriosView.as_view(), name='relatorios'),
    path('relatorios/compliance/', views.RelatorioComplianceView.as_view(), name='relatorio_compliance'),
    path('relatorios/vencimentos/', views.RelatorioVencimentosView.as_view(), name='relatorio_vencimentos'),
    path('relatorios/custos/', views.RelatorioCustosView.as_view(), name='relatorio_custos'),
    
    # =====================================
    # INTEGRAÇÕES
    # =====================================
    path('integracoes/', views.IntegracoesView.as_view(), name='integracoes'),
    path('anvisa/consultar/', views.ConsultarAnvisaView.as_view(), name='consultar_anvisa'),
    path('ofa/validar/', views.ValidarOFAView.as_view(), name='validar_ofa'),
    
    # =====================================
    # HISTÓRICO E AUDITORIA
    # =====================================
    path('historico/', views.HistoricoLicencasView.as_view(), name='historico'),
    path('auditoria/', views.AuditoriaLicencasView.as_view(), name='auditoria'),
    path('logs/', views.LogsLicencasView.as_view(), name='logs'),
    
    # =====================================
    # AJAX E UTILITÁRIOS
    # =====================================
    path('ajax/validar-numero/', views.ValidarNumeroLicencaView.as_view(), name='validar_numero'),
    path('ajax/calcular-vencimento/', views.CalcularVencimentoView.as_view(), name='calcular_vencimento'),
    path('ajax/buscar-orgao/', views.BuscarOrgaoView.as_view(), name='buscar_orgao'),
    
    # =====================================
    # API REST
    # =====================================
    path('api/', include(router.urls)),
    
    # API Personalizada
    path('api/verificar-status/', views.VerificarStatusAPIView.as_view(), name='api_verificar_status'),
    path('api/proximos-vencimentos/', views.ProximosVencimentosAPIView.as_view(), name='api_proximos_vencimentos'),
]