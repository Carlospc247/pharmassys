from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    # URLs do Catálogo de Serviços
    path('catalogo/', views.ServicoListView.as_view(), name='servico_list'),
    path('catalogo/novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('catalogo/<int:pk>/editar/', views.ServicoUpdateView.as_view(), name='servico_update'),
    path('catalogo/<int:pk>/eliminar/', views.ServicoDeleteView.as_view(), name='servico_delete'),

    path('api/listar/', views.listar_servicos_api, name='listar_servicos_api'),
    
    # URLs de Agendamentos
    path('', views.AgendamentoListView.as_view(), name='agendamento_list'),
    path('agendamentos/novo/', views.AgendamentoCreateView.as_view(), name='agendamento_create'),
    path('agendamentos/<int:pk>/editar/', views.AgendamentoUpdateView.as_view(), name='agendamento_update'),
    path('agendamentos/<int:pk>/eliminar/', views.AgendamentoDeleteView.as_view(), name='agendamento_delete'),
    
    path('agendamentos/<int:pk>/iniciar/', views.IniciarServicoView.as_view(), name='servico_iniciar'),
    path('agendamentos/<int:pk>/finalizar/', views.FinalizarServicoView.as_view(), name='servico_finalizar'),
]