"""# apps/estoque/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import MovimentacaoEstoque, Inventario, TransferenciaEstoque, Localizacao
from .serializers import MovimentacaoEstoqueSerializer, InventarioSerializer, TransferenciaEstoqueSerializer, LocalizacaoSerializer

class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentacaoEstoque.objects.all()
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_movimentacao', 'produto', 'loja']
    
    @action(detail=False, methods=['get'])
    def saldo_produto(self, request):
        produto_id = request.query_params.get('produto_id')
        if not produto_id:
            return Response({'error': 'produto_id requerido'}, status=400)
        
        # Calcular saldo atual
        movimentacoes = self.queryset.filter(produto_id=produto_id)
        saldo = sum(mov.quantidade if mov.tipo_movimentacao == 'entrada' else -mov.quantidade 
                   for mov in movimentacoes)
        
        return Response({'saldo': saldo})

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'loja']
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        inventario = self.get_object()
        inventario.status = 'finalizado'
        inventario.save()
        return Response({'status': 'inventário finalizado'})

class TransferenciaEstoqueViewSet(viewsets.ModelViewSet):
    queryset = TransferenciaEstoque.objects.all()
    serializer_class = TransferenciaEstoqueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'loja_origem', 'loja_destino']
"""


# apps/estoque/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import MovimentacaoEstoque, Inventario
from .serializers import MovimentacaoEstoqueSerializer, InventarioSerializer

class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentacaoEstoque.objects.all()
    serializer_class = MovimentacaoEstoqueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_movimentacao', 'produto', 'loja']
    
    @action(detail=False, methods=['get'])
    def saldo_produto(self, request):
        produto_id = request.query_params.get('produto_id')
        if not produto_id:
            return Response({'error': 'produto_id requerido'}, status=400)
        
        movimentacoes = self.queryset.filter(produto_id=produto_id)
        saldo = sum(
            mov.quantidade if mov.tipo_movimentacao.natureza == 'entrada' else -mov.quantidade 
            for mov in movimentacoes
        )
        return Response({'saldo': saldo})

    @action(detail=False, methods=['get'])
    def transferencias(self, request):
        """Lista apenas transferências de estoque"""
        transferencias = self.queryset.filter(tipo_movimentacao__natureza='transferencia')
        serializer = self.get_serializer(transferencias, many=True)
        return Response(serializer.data)


class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'loja']
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        inventario = self.get_object()
        inventario.status = 'concluido'
        inventario.save()
        return Response({'status': 'inventário finalizado'})
