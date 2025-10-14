from django.urls import path
from .views import CompraListView, CompraDetailView

app_name = "compras"

urlpatterns = [
    path('', CompraListView.as_view(), name='lista_compras'),
    path('<int:pk>/', CompraDetailView.as_view(), name='detalhe_compra'),
]
