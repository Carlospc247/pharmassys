# apps/comanda/urls.py
from django.urls import path
from . import views

app_name = 'comanda'

urlpatterns = [
    # =====================================
    # DASHBOARD E VISÃO GERAL
    # =====================================
    path('', views.ComandaDashboardView.as_view(), name='dashboard'),
    path('mapa-mesas/', views.MapaMesasView.as_view(), name='mapa_mesas'),
    path('lista/', views.ComandaListView.as_view(), name='lista'),
    
    # =====================================
    # GESTÃO DE MESAS
    # =====================================
    path('mesas/', views.MesaListView.as_view(), name='mesa_lista'),
    path('mesas/nova/', views.MesaCreateView.as_view(), name='mesa_create'),
    path('mesas/<int:pk>/', views.MesaDetailView.as_view(), name='mesa_detail'),
    path('mesas/<int:pk>/editar/', views.MesaUpdateView.as_view(), name='mesa_update'),
    path('mesas/<int:pk>/ocupar/', views.OcuparMesaView.as_view(), name='mesa_ocupar'),
    path('mesas/<int:pk>/liberar/', views.LiberarMesaView.as_view(), name='mesa_liberar'),
    
    # =====================================
    # GESTÃO DE COMANDAS
    # =====================================
    path('nova/', views.ComandaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ComandaDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ComandaUpdateView.as_view(), name='update'),
    path('<int:pk>/fechar/', views.FecharComandaView.as_view(), name='fechar'),
    path('<int:pk>/cancelar/', views.CancelarComandaView.as_view(), name='cancelar'),
    path('<int:pk>/reabrir/', views.ReabrirComandaView.as_view(), name='reabrir'),
    
    # =====================================
    # ITENS DA COMANDA
    # =====================================
    path('<int:comanda_pk>/item/adicionar/', views.AdicionarItemView.as_view(), name='adicionar_item'),
    path('item/<int:pk>/editar/', views.EditarItemView.as_view(), name='editar_item'),
    path('item/<int:pk>/remover/', views.RemoverItemView.as_view(), name='remover_item'),
    path('item/<int:pk>/cancelar/', views.CancelarItemView.as_view(), name='cancelar_item'),
    
    # =====================================
    # OPERAÇÕES FINANCEIRAS
    # =====================================
    path('<int:pk>/aplicar-desconto/', views.AplicarDescontoView.as_view(), name='aplicar_desconto'),
    path('<int:pk>/aplicar-acrescimo/', views.AplicarAcrescimoView.as_view(), name='aplicar_acrescimo'),
    path('<int:pk>/calcular-gorjeta/', views.CalcularGorjetaView.as_view(), name='calcular_gorjeta'),
    path('<int:pk>/dividir-conta/', views.DividirContaView.as_view(), name='dividir_conta'),
    
    # =====================================
    # TRANSFERÊNCIAS
    # =====================================
    path('<int:pk>/transferir-mesa/', views.TransferirMesaView.as_view(), name='transferir_mesa'),
    path('<int:pk>/transferir-garcom/', views.TransferirGarcomView.as_view(), name='transferir_garcom'),
    path('itens/transferir/', views.TransferirItensView.as_view(), name='transferir_itens'),
    
    # =====================================
    # RELATÓRIOS
    # =====================================
    path('relatorios/', views.ComandaRelatoriosView.as_view(), name='relatorios'),
    path('relatorios/vendas-mesa/', views.RelatorioVendasMesaView.as_view(), name='relatorio_vendas_mesa'),
    path('relatorios/tempo-atendimento/', views.RelatorioTempoAtendimentoView.as_view(), name='relatorio_tempo'),
    path('relatorios/produtos-mais-vendidos/', views.RelatorioProdutosMaisVendidosView.as_view(), name='relatorio_produtos'),
    
    # =====================================
    # CONFIGURAÇÕES
    # =====================================
    path('configuracoes/', views.ConfiguracaoComandaView.as_view(), name='configuracoes'),
    path('layout-mesas/', views.LayoutMesasView.as_view(), name='layout_mesas'),
    
    # =====================================
    # IMPRESSÃO
    # =====================================
    path('<int:pk>/imprimir/', views.ImprimirComandaView.as_view(), name='imprimir'),
    path('<int:pk>/imprimir-conta/', views.ImprimirContaView.as_view(), name='imprimir_conta'),
    path('<int:pk>/imprimir-cupom/', views.ImprimirCupomView.as_view(), name='imprimir_cupom'),
    
    # =====================================
    # AJAX E UTILITÁRIOS
    # =====================================
    path('ajax/status-mesa/', views.StatusMesaAjaxView.as_view(), name='status_mesa_ajax'),
    path('ajax/calcular-total/', views.CalcularTotalAjaxView.as_view(), name='calcular_total_ajax'),
    path('ajax/buscar-produto/', views.BuscarProdutoComandaView.as_view(), name='buscar_produto'),
    path('ajax/atualizar-mesa/', views.AtualizarMesaAjaxView.as_view(), name='atualizar_mesa_ajax'),

    # =====================================
# URLS DE MESAS - ADICIONAR AO ARQUIVO DE URLS EXISTENTE
# =====================================

# Gestão de Mesas
path('mesas/', views.MesaListView.as_view(), name='mesa_lista'),
path('mesas/nova/', views.MesaCreateView.as_view(), name='mesa_create'),
path('mesas/<int:pk>/', views.MesaDetailView.as_view(), name='mesa_detail'),
path('mesas/<int:pk>/editar/', views.MesaUpdateView.as_view(), name='mesa_update'),
path('mesas/<int:pk>/deletar/', views.MesaDeleteView.as_view(), name='mesa_delete'),
path('mesas/<int:pk>/ocupar/', views.OcuparMesaView.as_view(), name='mesa_ocupar'),
path('mesas/<int:pk>/liberar/', views.LiberarMesaView.as_view(), name='mesa_liberar'),
path('mesas/<int:pk>/reservar/', views.ReservarMesaView.as_view(), name='mesa_reservar'),
path('mesas/<int:pk>/gerar-qr/', views.GerarQRCodeMesaView.as_view(), name='mesa_gerar_qr'),

# AJAX para Mesas
path('ajax/mesa-status/', views.MesaStatusAjaxView.as_view(), name='mesa_status_ajax'),
]