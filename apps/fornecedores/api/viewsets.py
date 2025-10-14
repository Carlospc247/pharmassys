# apps/fornecedores/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Fornecedor, ContatoFornecedor, Pedido, AvaliacaoFornecedor
from .serializers import FornecedorSerializer, ContatoFornecedorSerializer, PedidoCompraSerializer, AvaliacaoFornecedorSerializer

class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ativo', 'tipo_fornecedor']
    
    @action(detail=True, methods=['get'])
    def avaliacoes(self, request, pk=None):
        fornecedor = self.get_object()
        avaliacoes = fornecedor.avaliacoes.all()
        serializer = AvaliacaoFornecedorSerializer(avaliacoes, many=True)
        return Response(serializer.data)

class PedidoCompraViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoCompraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'fornecedor']
    
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        pedido = self.get_object()
        pedido.status = 'aprovado'
        pedido.save()
        return Response({'status': 'pedido aprovado'})

class ContatoFornecedorViewSet(viewsets.ModelViewSet):
    queryset = ContatoFornecedor.objects.all()
    serializer_class = ContatoFornecedorSerializer
    permission_classes = [permissions.IsAuthenticated]