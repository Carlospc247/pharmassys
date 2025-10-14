# apps/vendas/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Venda, ItemVenda, PagamentoVenda, DevolucaoVenda
from .serializers import VendaSerializer, ItemVendaSerializer, PagamentoSerializer, DevolucaoSerializer


class VendaViewSet(viewsets.ModelViewSet):
    queryset = Venda.objects.all()
    serializer_class = VendaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'cliente', 'vendedor', 'data_venda']
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        venda = self.get_object()
        venda.status = 'finalizada'
        venda.save()
        return Response({'status': 'venda finalizada'})
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        venda = self.get_object()
        venda.status = 'cancelada'
        venda.save()
        return Response({'status': 'venda cancelada'})

class ItemVendaViewSet(viewsets.ModelViewSet):
    queryset = ItemVenda.objects.all()
    serializer_class = ItemVendaSerializer
    permission_classes = [permissions.IsAuthenticated]

class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = PagamentoVenda.objects.all() #queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]



