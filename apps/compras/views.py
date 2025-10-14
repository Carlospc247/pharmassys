from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Compra

# Lista todas as compras com filtros simples
class CompraListView(ListView):
    model = Compra
    template_name = "compras/compra_list.html"  # Crie esta pasta/template
    context_object_name = "compras"
    paginate_by = 25
    ordering = ['-data']

    def get_queryset(self):
        queryset = super().get_queryset()
        fornecedor = self.request.GET.get('fornecedor')
        if fornecedor:
            queryset = queryset.filter(fornecedor__nome__icontains=fornecedor)
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data__date__lte=data_fim)
        return queryset

# Detalhes de uma compra específica
class CompraDetailView(DetailView):
    model = Compra
    template_name = "compras/compra_detail.html"  # Crie esta pasta/template
    context_object_name = "compra"

