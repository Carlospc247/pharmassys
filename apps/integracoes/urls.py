from django.urls import path
from . import views

app_name = 'bar'

urlpatterns = [
    path('dashboard/', views.dashboard_bar, name='dashboard'),
    # Produtos
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('produtos/novo/', views.criar_produto, name='criar_produto'),
    path('produtos/<int:pk>/editar/', views.editar_produto, name='editar_produto'),

    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/novo/', views.criar_categoria, name='criar_categoria'),

    # Comandas
    path('comandas/', views.lista_comandas, name='lista_comandas'),
    path('comandas/abrir/', views.abrir_comanda, name='abrir_comanda'),
    path('comandas/<int:pk>/fechar/', views.fechar_comanda, name='fechar_comanda'),

    # Cozinha (Pedidos)
    path('cozinha/pedidos/', views.pedidos_cozinha, name='pedidos_cozinha'),

    
]
