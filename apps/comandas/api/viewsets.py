# apps/comanda/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.db.models import Sum, Count
from ..models import Mesa, Comanda, ItemComanda, StatusComanda
from .serializers import MesaSerializer, ComandaSerializer, ItemComandaSerializer

class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['numero', 'descricao']
    filterset_fields = ['status', 'ativa', 'loja', 'localizacao']
    ordering = ['numero']
    
    @action(detail=False, methods=['get'])
    def mapa_mesas(self, request):
        """Retorna layout das mesas com status atual"""
        loja_id = request.query_params.get('loja_id')
        
        queryset = self.queryset
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        
        mesas_data = []
        for mesa in queryset.filter(ativa=True):
            # Buscar comanda ativa
            comanda_ativa = mesa.comandas.filter(
                status__in=['aberta', 'em_andamento']
            ).first()
            
            mesa_info = {
                'id': mesa.id,
                'numero': mesa.numero,
                'capacidade': mesa.capacidade,
                'status': mesa.status,
                'localizacao': mesa.localizacao,
                'coordenada_x': mesa.coordenada_x,
                'coordenada_y': mesa.coordenada_y,
                'comanda_ativa': None
            }
            
            if comanda_ativa:
                mesa_info['comanda_ativa'] = {
                    'id': comanda_ativa.id,
                    'numero_comanda': comanda_ativa.numero_comanda,
                    'total': comanda_ativa.total,
                    'tempo_mesa': self._calcular_tempo_mesa(comanda_ativa),
                    'total_itens': comanda_ativa.itens.count()
                }
            
            mesas_data.append(mesa_info)
        
        return Response(mesas_data)
    
    def _calcular_tempo_mesa(self, comanda):
        """Calcula tempo que a mesa está ocupada"""
        if comanda.data_abertura:
            delta = timezone.now() - comanda.data_abertura
            horas = delta.total_seconds() // 3600
            minutos = (delta.total_seconds() % 3600) // 60
            return f"{int(horas)}h {int(minutos)}m"
        return "0h 0m"
    
    @action(detail=True, methods=['post'])
    def ocupar_mesa(self, request, pk=None):
        """Ocupa uma mesa disponível"""
        mesa = self.get_object()
        
        if mesa.status != 'disponivel':
            return Response(
                {'error': 'Mesa não está disponível'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mesa.status = 'ocupada'
        mesa.save()
        
        # Criar nova comanda
        comanda = Comanda.objects.create(
            mesa=mesa,
            funcionario_id=request.data.get('funcionario_id', request.user.id),
            cliente_id=request.data.get('cliente_id'),
            loja=mesa.loja
        )
        
        return Response({
            'mesa': self.get_serializer(mesa).data,
            'comanda': ComandaSerializer(comanda).data
        })
    
    @action(detail=True, methods=['post'])
    def liberar_mesa(self, request, pk=None):
        """Libera uma mesa ocupada"""
        mesa = self.get_object()
        
        # Verificar se há comanda ativa
        comanda_ativa = mesa.comandas.filter(
            status__in=['aberta', 'em_andamento']
        ).first()
        
        if comanda_ativa:
            return Response(
                {'error': 'Mesa possui comanda ativa. Finalize a comanda primeiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mesa.status = 'disponivel'
        mesa.save()
        
        return Response(self.get_serializer(mesa).data)

class ComandaViewSet(viewsets.ModelViewSet):
    queryset = Comanda.objects.all()
    serializer_class = ComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['numero_comanda', 'cliente__nome', 'mesa__numero']
    filterset_fields = [
        'status', 'mesa', 'funcionario', 'data_abertura', 'loja'
    ]
    ordering = ['-data_abertura']
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'mesa', 'cliente', 'funcionario', 'loja'
        ).prefetch_related('itens__produto')
    
    @action(detail=True, methods=['post'])
    def adicionar_item(self, request, pk=None):
        """Adiciona item à comanda"""
        comanda = self.get_object()
        
        if comanda.status not in ['aberta', 'em_andamento']:
            return Response(
                {'error': 'Comanda não está aberta para novos itens'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        produto_id = request.data.get('produto_id')
        quantidade = request.data.get('quantidade', 1)
        observacoes = request.data.get('observacoes', '')
        
        if not produto_id:
            return Response(
                {'error': 'produto_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.produtos.models import Produto
            produto = Produto.objects.get(id=produto_id)
            
            # Buscar preço atual
            preco_atual = produto.preco_atual()
            if not preco_atual:
                return Response(
                    {'error': 'Produto sem preço cadastrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Criar item
            item = ItemComanda.objects.create(
                comanda=comanda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco_atual,
                observacoes=observacoes
            )
            
            # Atualizar totais da comanda
            self._atualizar_totais_comanda(comanda)
            
            serializer = ItemComandaSerializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Produto.DoesNotExist:
            return Response(
                {'error': 'Produto não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _atualizar_totais_comanda(self, comanda):
        """Atualiza os totais da comanda"""
        itens = comanda.itens.all()
        
        valor_subtotal = sum(item.total for item in itens)
        total = valor_subtotal - comanda.valor_desconto + comanda.valor_acrescimo
        
        comanda.valor_subtotal = valor_subtotal
        comanda.total = total
        comanda.save()
    
    @action(detail=True, methods=['post'])
    def aplicar_desconto(self, request, pk=None):
        """Aplica desconto à comanda"""
        comanda = self.get_object()
        
        tipo_desconto = request.data.get('tipo_desconto', 'valor')  # 'valor' ou 'percentual'
        valor_desconto = float(request.data.get('valor_desconto', 0))
        motivo = request.data.get('motivo_desconto', '')
        
        if tipo_desconto == 'percentual':
            if valor_desconto > 100:
                return Response(
                    {'error': 'Percentual não pode ser maior que 100%'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            comanda.valor_desconto = (comanda.valor_subtotal * valor_desconto) / 100
        else:
            comanda.valor_desconto = valor_desconto
        
        comanda.observacoes += f"\nDesconto aplicado: {motivo}"
        
        # Recalcular total
        self._atualizar_totais_comanda(comanda)
        
        return Response(self.get_serializer(comanda).data)
    
    @action(detail=True, methods=['post'])
    def fechar_comanda(self, request, pk=None):
        """Fecha a comanda e libera a mesa"""
        comanda = self.get_object()
        
        if comanda.status == 'fechada':
            return Response(
                {'error': 'Comanda já está fechada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se há itens
        if not comanda.itens.exists():
            return Response(
                {'error': 'Comanda não possui itens'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aplicar gorjeta se informada
        gorjeta = request.data.get('gorjeta', 0)
        if gorjeta:
            comanda.gorjeta = float(gorjeta)
            comanda.total += comanda.gorjeta
        
        # Fechar comanda
        comanda.status = 'fechada'
        comanda.data_fechamento = timezone.now()
        comanda.save()
        
        # Liberar mesa
        comanda.mesa.status = 'disponivel'
        comanda.mesa.save()
        
        # Registrar mudança de status
        StatusComanda.objects.create(
            comanda=comanda,
            status_anterior='aberta',
            status_novo='fechada',
            usuario=request.user,
            observacoes='Comanda fechada pelo usuário'
        )
        
        return Response(self.get_serializer(comanda).data)
    
    @action(detail=True, methods=['post'])
    def transferir_mesa(self, request, pk=None):
        """Transfere comanda para outra mesa"""
        comanda = self.get_object()
        nova_mesa_id = request.data.get('nova_mesa_id')
        
        if not nova_mesa_id:
            return Response(
                {'error': 'nova_mesa_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            nova_mesa = Mesa.objects.get(id=nova_mesa_id)
            
            if nova_mesa.status != 'disponivel':
                return Response(
                    {'error': 'Mesa de destino não está disponível'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Liberar mesa atual
            mesa_anterior = comanda.mesa
            mesa_anterior.status = 'disponivel'
            mesa_anterior.save()
            
            # Ocupar nova mesa
            nova_mesa.status = 'ocupada'
            nova_mesa.save()
            
            # Atualizar comanda
            comanda.mesa = nova_mesa
            comanda.observacoes += f"\nTransferida da mesa {mesa_anterior.numero} para {nova_mesa.numero}"
            comanda.save()
            
            return Response(self.get_serializer(comanda).data)
            
        except Mesa.DoesNotExist:
            return Response(
                {'error': 'Mesa de destino não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def comandas_abertas(self, request):
        """Retorna comandas abertas"""
        comandas = self.queryset.filter(
            status__in=['aberta', 'em_andamento']
        )
        
        loja_id = request.query_params.get('loja_id')
        if loja_id:
            comandas = comandas.filter(loja_id=loja_id)
        
        serializer = self.get_serializer(comandas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def relatorio_vendas(self, request):
        """Relatório de vendas por período"""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        queryset = self.queryset.filter(status='fechada')
        
        if data_inicio:
            queryset = queryset.filter(data_fechamento__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_fechamento__date__lte=data_fim)
        
        # Estatísticas
        estatisticas = queryset.aggregate(
            total_comandas=Count('id'),
            total=Sum('total'),
            valor_gorjetas=Sum('gorjeta')
        )
        
        # Vendas por mesa
        vendas_por_mesa = queryset.values('mesa__numero').annotate(
            total_vendas=Sum('total'),
            total_comandas=Count('id')
        ).order_by('-total_vendas')
        
        return Response({
            'estatisticas': estatisticas,
            'vendas_por_mesa': list(vendas_por_mesa)
        })

class ItemComandaViewSet(viewsets.ModelViewSet):
    queryset = ItemComanda.objects.all()
    serializer_class = ItemComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['comanda', 'produto', 'status_item']
    
    @action(detail=True, methods=['post'])
    def cancelar_item(self, request, pk=None):
        """Cancela um item da comanda"""
        item = self.get_object()
        
        if item.status_item == 'cancelado':
            return Response(
                {'error': 'Item já está cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if item.comanda.status not in ['aberta', 'em_andamento']:
            return Response(
                {'error': 'Não é possível cancelar item de comanda fechada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo_cancelamento', 'Cancelado pelo usuário')
        
        item.status_item = 'cancelado'
        item.observacoes += f"\nCancelado: {motivo}"
        item.save()
        
        # Recalcular totais da comanda
        comanda = item.comanda
        itens_ativos = comanda.itens.exclude(status_item='cancelado')
        
        valor_subtotal = sum(i.total for i in itens_ativos)
        total = valor_subtotal - comanda.valor_desconto + comanda.valor_acrescimo
        
        comanda.valor_subtotal = valor_subtotal
        comanda.total = total
        comanda.save()
        
        return Response(self.get_serializer(item).data)