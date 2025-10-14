# apps/fornecedores/filters.py
import django_filters
from django.db.models import Q
from .models import Fornecedor, Pedido


class FornecedorFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(
        method='filter_nome',
        label='Nome',
        help_text='Busca por nome fantasia ou razão social'
    )
    
    avaliacao_min = django_filters.NumberFilter(
        field_name='nota_avaliacao',
        lookup_expr='gte',
        label='Avaliação mínima'
    )
    
    prazo_entrega_max = django_filters.NumberFilter(
        field_name='prazo_entrega_dias',
        lookup_expr='lte',
        label='Prazo máximo de entrega (dias)'
    )
    
    tem_pedidos_pendentes = django_filters.BooleanFilter(
        method='filter_pedidos_pendentes',
        label='Possui pedidos pendentes'
    )

    status = django_filters.ChoiceFilter(
        field_name='ativo',
        choices=[(True, 'Ativo'), (False, 'Inativo')],
        label='Status'
    )
    
    tipo_fornecedor = django_filters.ChoiceFilter(
        field_name='categoria',
        choices=Fornecedor.CATEGORIA_CHOICES,
        label='Tipo de fornecedor'
    )
    
    class Meta:
        model = Fornecedor
        fields = {
            'cidade': ['icontains'],
            'provincia': ['exact'],
        }
    
    def filter_nome(self, queryset, name, value):
        return queryset.filter(
            Q(nome_fantasia__icontains=value) |
            Q(razao_social__icontains=value)
        )
    
    def filter_pedidos_pendentes(self, queryset, name, value):
        if value:
            return queryset.filter(
                pedidos__status__in=['enviado', 'confirmado', 'entregue_parcial']
            ).distinct()
        return queryset


class PedidoCompraFilter(django_filters.FilterSet):
    data_pedido_inicio = django_filters.DateFilter(
        field_name='data_pedido',
        lookup_expr='gte',
        label='Data pedido - início'
    )
    
    data_pedido_fim = django_filters.DateFilter(
        field_name='data_pedido',
        lookup_expr='lte',
        label='Data pedido - fim'
    )
    
    valor_min = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='gte',
        label='Valor mínimo'
    )
    
    valor_max = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='lte',
        label='Valor máximo'
    )
    
    atrasado = django_filters.BooleanFilter(
        method='filter_atrasado',
        label='Pedidos atrasados'
    )
    
    class Meta:
        model = Pedido
        fields = {
            'fornecedor': ['exact'],
            'status': ['exact'],
            #'tipo_pedido': ['exact'],
        }
    
    def filter_atrasado(self, queryset, name, value):
        if value:
            from datetime import date
            return queryset.filter(
                status__in=['enviado', 'confirmado', 'entregue_parcial'],
                data_prevista_entrega__lt=date.today()
            )
        return queryset


