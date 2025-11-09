from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    # URLs do Catálogo de Serviços
    path('catalogo/', views.ServicoDashboard.as_view(), name='servico_dashboard'),
    path('catalogo/', views.ServicoListView.as_view(), name='servico_list'),
    path('catalogo/novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('catalogo/<int:pk>/editar/', views.ServicoUpdateView.as_view(), name='servico_update'),
    path('catalogo/<int:pk>/eliminar/', views.ServicoDeleteView.as_view(), name='servico_delete'),

    path('api/listar/', views.listar_servicos_api, name='listar_servicos_api'),
    path('api/buscar/', views.buscar_servicos_api, name='buscar_servicos_api'),

    # URLs de Agendamentos
    path('', views.AgendamentoListView.as_view(), name='agendamento_list'),
    path('agendamentos/novo/', views.AgendamentoCreateView.as_view(), name='agendamento_create'),
    path('agendamentos/<int:pk>/editar/', views.AgendamentoUpdateView.as_view(), name='agendamento_update'),
    path('agendamentos/<int:pk>/eliminar/', views.AgendamentoDeleteView.as_view(), name='agendamento_delete'),
    path('api/agendamentos/buscar/', views.buscar_agendamento_api, name='buscar_agendamento_api'),


    path('agendamentos/<int:pk>/iniciar/', views.IniciarServicoView.as_view(), name='servico_iniciar'),
    path('agendamentos/<int:pk>/finalizar/', views.FinalizarServicoView.as_view(), name='servico_finalizar'),


    path('', views.notificacao_list, name='notificacao_list'),
    path('criar/', views.notificacao_create, name='notificacao_create'),
    path('<int:pk>/editar/', views.notificacao_update, name='notificacao_update'),
    path('<int:pk>/deletar/', views.notificacao_delete, name='notificacao_delete'),
    path('api/buscar/', views.buscar_notificacao_api, name='buscar_notificacao_api'),

    # Configurações
    #path('config/', views.config_notificacao_view, name='config_notificacao'),
    path('config/', views.configuracao_notificacao_update, name='config_notificacao'),
    

    
]