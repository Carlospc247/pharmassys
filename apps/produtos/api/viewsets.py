

# apps/produtos/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from ..models import Categoria, Fabricante, Produto, Lote, Preco
from .serializers import (
    CategoriaSerializer, FabricanteSerializer, ProdutoSerializer,
    LoteSerializer, PrecoSerializer
)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']

class FabricanteViewSet(viewsets.ModelViewSet):
    queryset = Fabricante.objects.all()
    serializer_class = FabricanteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['nome', 'nif']
    filterset_fields = ['ativo']

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['nome_comercial', 'codigo_barras']
    filterset_fields = ['categoria', 'fabricante', 'ativo']
    
    @action(detail=True, methods=['get'])
    def preco_atual(self, request, pk=None):
        """Retorna o preço atual do produto"""
        produto = self.get_object()
        try:
            preco = produto.precos.filter(ativo=True).latest('data_inicio')
            serializer = PrecoSerializer(preco)
            return Response(serializer.data)
        except Preco.DoesNotExist:
            return Response(
                {'error': 'Preço não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def estoque_disponivel(self, request, pk=None):
        """Retorna estoque disponível do produto"""
        produto = self.get_object()
        # Implementar lógica de cálculo de estoque
        estoque = produto.calcular_estoque_disponivel()
        return Response({'estoque_disponivel': estoque})

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['numero_lote', 'produto__nome_comercial']
    filterset_fields = ['produto', 'vencido']
    
    @action(detail=False, methods=['get'])
    def vencimentos_proximos(self, request):
        """Retorna lotes com vencimento próximo"""
        from datetime import date, timedelta
        
        dias = int(request.query_params.get('dias', 30))
        data_limite = date.today() + timedelta(days=dias)
        
        lotes = self.queryset.filter(
            data_vencimento__lte=data_limite,
            data_vencimento__gte=date.today()
        )
        
        serializer = self.get_serializer(lotes, many=True)
        return Response(serializer.data)

class PrecoViewSet(viewsets.ModelViewSet):
    queryset = Preco.objects.all()
    serializer_class = PrecoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['produto', 'ativo']
