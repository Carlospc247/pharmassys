# apps/servicos/api/viewsets.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from datetime import date, timedelta
from ..models import (
    Servico, AplicacaoVacina, TesteRapido,
    AfericaoParametros, ConsultoriaFarmaceutica, AgendamentoServico
)
from .serializers import (
     ServicoSerializer, AplicacaoVacinaSerializer,
    TesteRapidoSerializer
)


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = [
        'numero_servico', 'paciente__numero_prontuario',
        'paciente__cliente__nome'
    ]
    filterset_fields = [
        'servico', 'status', 'farmaceutico',
        'data_agendamento', 'paciente'
    ]
    ordering = ['-data_agendamento']
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'servico', 'paciente__cliente', 'farmaceutico'
        )
    
    @action(detail=True, methods=['post'])
    def iniciar_servico(self, request, pk=None):
        """Inicia a realização do serviço"""
        servico = self.get_object()
        
        if servico.status != 'agendado':
            return Response(
                {'error': 'Serviço não está agendado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        servico.status = 'em_andamento'
        servico.save()
        
        serializer = self.get_serializer(servico)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def finalizar_servico(self, request, pk=None):
        """Finaliza a realização do serviço"""
        servico = self.get_object()
        
        if servico.status != 'em_andamento':
            return Response(
                {'error': 'Serviço não está em andamento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        servico.status = 'concluido'
        servico.data_realizacao = timezone.now()
        
        # Campos opcionais
        if 'resultado_servico' in request.data:
            servico.resultado_servico = request.data['resultado_servico']
        if 'recomendacoes' in request.data:
            servico.recomendacoes = request.data['recomendacoes']
        if 'observacoes_realizacao' in request.data:
            servico.observacoes_realizacao = request.data['observacoes_realizacao']
        
        servico.save()
        
        serializer = self.get_serializer(servico)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancelar_servico(self, request, pk=None):
        """Cancela o serviço"""
        servico = self.get_object()
        
        if servico.status in ['concluido', 'cancelado']:
            return Response(
                {'error': 'Serviço não pode ser cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        servico.status = 'cancelado'
        servico.observacoes_realizacao = request.data.get(
            'motivo_cancelamento', 'Cancelado pelo usuário'
        )
        servico.save()
        
        serializer = self.get_serializer(servico)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def avaliar_servico(self, request, pk=None):
        """Permite ao cliente avaliar o serviço"""
        servico = self.get_object()
        
        if servico.status != 'concluido':
            return Response(
                {'error': 'Serviço deve estar concluído para avaliação'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        avaliacao = request.data.get('avaliacao_cliente')
        comentario = request.data.get('comentario_cliente', '')
        
        if not avaliacao or not (1 <= int(avaliacao) <= 5):
            return Response(
                {'error': 'Avaliação deve ser entre 1 e 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        servico.avaliacao_cliente = avaliacao
        servico.comentario_cliente = comentario
        servico.save()
        
        return Response({'status': 'avaliação registrada'})
    
    @action(detail=False, methods=['get'])
    def agenda_farmaceutico(self, request):
        """Retorna agenda de serviços do farmacêutico"""
        farmaceutico_id = request.query_params.get('farmaceutico_id')
        data = request.query_params.get('data')
        
        if not farmaceutico_id:
            return Response(
                {'error': 'farmaceutico_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.queryset.filter(farmaceutico_id=farmaceutico_id)
        
        if data:
            queryset = queryset.filter(data_agendamento__date=data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AplicacaoVacinaViewSet(viewsets.ModelViewSet):
    queryset = AplicacaoVacina.objects.all()
    serializer_class = AplicacaoVacinaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'servico__paciente', 'vacina', 'local_aplicacao',
        'teve_reacao', 'servico__data_realizacao'
    ]
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'servico__paciente__cliente', 'vacina'
        )
    
    @action(detail=False, methods=['get'])
    def cartao_vacina(self, request):
        """Gera cartão de vacinação do paciente"""
        paciente_id = request.query_params.get('paciente_id')
        
        if not paciente_id:
            return Response(
                {'error': 'paciente_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vacinas = self.queryset.filter(
            servico__paciente_id=paciente_id
        ).order_by('servico__data_realizacao')
        
        cartao = []
        for vacina in vacinas:
            cartao.append({
                'vacina': vacina.vacina.nome_comercial,
                'data_aplicacao': vacina.servico.data_realizacao,
                'lote': vacina.lote_vacina,
                'dose_ml': vacina.dose_ml,
                'local_aplicacao': vacina.local_aplicacao,
                'farmaceutico': vacina.servico.farmaceutico.nome,
                'proxima_dose': vacina.proxima_dose_data
            })
        
        return Response(cartao)

class TesteRapidoViewSet(viewsets.ModelViewSet):
    queryset = TesteRapido.objects.all()
    serializer_class = TesteRapidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'tipo_teste', 'resultado', 'servico__paciente',
        'servico__data_realizacao'
    ]
    
    @action(detail=False, methods=['get'])
    def estatisticas_resultado(self, request):
        """Estatísticas de resultados por tipo de teste"""
        tipo_teste = request.query_params.get('tipo_teste')
        
        queryset = self.queryset
        if tipo_teste:
            queryset = queryset.filter(tipo_teste=tipo_teste)
        
        # Contar resultados
        from django.db.models import Count
        
        estatisticas = queryset.values('resultado').annotate(
            total=Count('id')
        )
        
        return Response(list(estatisticas))

# apps/comandas/api/viewsets.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, timedelta

from ..models import (
    Comanda, ItemComanda, ProdutoComanda, CategoriaComanda,
    Mesa, Pagamento, CentroRequisicao, MovimentacaoComanda
)
from .serializers import (
    ComandaSerializer, ComandaResumoSerializer, ItemComandaSerializer,
    ProdutoComandaSerializer, CategoriaComandaSerializer, MesaSerializer,
    PagamentoSerializer, CentroRequisicaoSerializer, MovimentacaoComandaSerializer
)

class ComandaViewSet(viewsets.ModelViewSet):
    serializer_class = ComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tipo_atendimento', 'mesa']
    search_fields = ['numero_comanda', 'cliente__nome']
    ordering_fields = ['data_abertura', 'total']
    ordering = ['-data_abertura']
    
    def get_queryset(self):
        return Comanda.objects.filter(
            empresa=self.request.user.empresa
        ).select_related('mesa', 'cliente', 'atendente').prefetch_related('itens', 'pagamentos')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ComandaResumoSerializer
        return ComandaSerializer
    
    def perform_create(self, serializer):
        comanda = serializer.save(empresa=self.request.user.empresa)
        
        # Ocupar mesa se selecionada
        if comanda.mesa:
            comanda.mesa.ocupar_mesa()
        
        # Registrar movimentação
        MovimentacaoComanda.registrar_movimentacao(
            comanda=comanda,
            tipo_movimentacao='abertura',
            descricao=f'Comanda criada via API por {self.request.user.nome}',
            usuario=self.request.user,
            request=self.request
        )
    
    @action(detail=True, methods=['post'])
    def adicionar_item(self, request, pk=None):
        comanda = self.get_object()
        
        produto_id = request.data.get('produto_id')
        quantidade = int(request.data.get('quantidade', 1))
        observacoes = request.data.get('observacoes', '')
        
        try:
            produto = ProdutoComanda.objects.get(
                id=produto_id, 
                empresa=request.user.empresa
            )
            
            valor_anterior = comanda.total
            comanda.adicionar_item(produto, quantidade, observacoes)
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='adicao_item',
                descricao=f'Adicionado {quantidade}x {produto.nome} via API',
                usuario=request.user,
                valor_anterior=valor_anterior,
                valor_atual=comanda.total,
                request=request
            )
            
            return Response({
                'success': True,
                'message': f'{quantidade}x {produto.nome} adicionado à comanda',
                'comanda': ComandaSerializer(comanda).data
            })
            
        except ProdutoComanda.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Produto não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def adicionar_pagamento(self, request, pk=None):
        comanda = self.get_object()
        
        serializer = PagamentoSerializer(data=request.data)
        if serializer.is_valid():
            pagamento = serializer.save(comanda=comanda)
            
            # Atualizar valor pago
            comanda.valor_pago += pagamento.valor
            comanda.save()
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='pagamento',
                descricao=f'Pagamento {pagamento.get_forma_pagamento_display()} - R$ {pagamento.valor} via API',
                usuario=request.user,
                pagamento_relacionado=pagamento,
                request=request
            )
            
            # Verificar se foi totalmente paga
            if comanda.valor_pago >= comanda.total:
                comanda.status = 'entregue'
                comanda.save()
            
            return Response({
                'success': True,
                'message': 'Pagamento registrado com sucesso',
                'pagamento': PagamentoSerializer(pagamento).data,
                'comanda': ComandaSerializer(comanda).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def fechar_comanda(self, request, pk=None):
        comanda = self.get_object()
        
        try:
            comanda.fechar_comanda()
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='fechamento',
                descricao=f'Comanda fechada via API por {request.user.nome}',
                usuario=request.user,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Comanda fechada com sucesso',
                'comanda': ComandaSerializer(comanda).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False)
    def abertas(self, request):
        """Retorna comandas em aberto"""
        comandas = self.get_queryset().filter(
            status__in=['aberta', 'em_preparo', 'pronta']
        )
        serializer = ComandaResumoSerializer(comandas, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def dashboard(self, request):
        """Dados para dashboard"""
        hoje = date.today()
        comandas_hoje = self.get_queryset().filter(data_abertura__date=hoje)
        
        stats = {
            'comandas_abertas': comandas_hoje.filter(status='aberta').count(),
            'comandas_em_preparo': comandas_hoje.filter(status='em_preparo').count(),
            'comandas_prontas': comandas_hoje.filter(status='pronta').count(),
            'comandas_fechadas': comandas_hoje.filter(status='fechada').count(),
            'faturamento_dia': comandas_hoje.filter(status='fechada').aggregate(
                total=Sum('total')
            )['total'] or 0,
        }
        
        return Response(stats)

class ItemComandaViewSet(viewsets.ModelViewSet):
    serializer_class = ItemComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'produto']
    ordering = ['hora_pedido']
    
    def get_queryset(self):
        return ItemComanda.objects.filter(
            comanda__empresa=self.request.user.empresa
        ).select_related('comanda', 'produto')
    
    @action(detail=True, methods=['post'])
    def iniciar_preparo(self, request, pk=None):
        item = self.get_object()
        
        try:
            item.iniciar_preparo()
            
            # Atualizar comanda se necessário
            if item.comanda.status == 'aberta':
                item.comanda.status = 'em_preparo'
                item.comanda.save()
            
            return Response({
                'success': True,
                'message': f'Preparo iniciado: {item.produto.nome}',
                'item': ItemComandaSerializer(item).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def finalizar_preparo(self, request, pk=None):
        item = self.get_object()
        
        try:
            item.finalizar_preparo()
            
            # Verificar se todos estão prontos
            itens_nao_prontos = item.comanda.itens.exclude(status__in=['pronto', 'entregue'])
            if not itens_nao_prontos.exists():
                item.comanda.status = 'pronta'
                item.comanda.save()
            
            return Response({
                'success': True,
                'message': f'Item finalizado: {item.produto.nome}',
                'item': ItemComandaSerializer(item).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False)
    def cozinha(self, request):
        """Itens para cozinha"""
        itens = self.get_queryset().filter(
            status__in=['pendente', 'em_preparo']
        ).order_by('hora_pedido')
        
        serializer = self.get_serializer(itens, many=True)
        return Response(serializer.data)

class ProdutoComandaViewSet(viewsets.ModelViewSet):
    serializer_class = ProdutoComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'disponivel', 'destaque']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'preco_venda']
    ordering = ['categoria', 'nome']
    
    def get_queryset(self):
        return ProdutoComanda.objects.filter(
            empresa=self.request.user.empresa
        ).select_related('categoria')
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=False)
    def disponiveis(self, request):
        """Produtos disponíveis"""
        produtos = self.get_queryset().filter(disponivel=True)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def por_categoria(self, request):
        """Produtos agrupados por categoria"""
        categorias = CategoriaComanda.objects.filter(
            empresa=request.user.empresa,
            ativa=True
        ).prefetch_related('produtocomanda_set')
        
        resultado = []
        for categoria in categorias:
            produtos = categoria.produtocomanda_set.filter(disponivel=True)
            resultado.append({
                'categoria': CategoriaComandaSerializer(categoria).data,
                'produtos': ProdutoComandaSerializer(produtos, many=True).data
            })
        
        return Response(resultado)

class CategoriaComandaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaComandaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['ordem_exibicao', 'nome']
    
    def get_queryset(self):
        return CategoriaComanda.objects.filter(empresa=self.request.user.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)

class MesaViewSet(viewsets.ModelViewSet):
    serializer_class = MesaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'ativa']
    ordering = ['numero']
    
    def get_queryset(self):
        return Mesa.objects.filter(empresa=self.request.user.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=False)
    def livres(self, request):
        """Mesas livres"""
        mesas = self.get_queryset().filter(status='livre', ativa=True)
        serializer = self.get_serializer(mesas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ocupar(self, request, pk=None):
        mesa = self.get_object()
        
        try:
            mesa.ocupar_mesa()
            return Response({
                'success': True,
                'message': f'Mesa {mesa.numero} ocupada',
                'mesa': MesaSerializer(mesa).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def liberar(self, request, pk=None):
        mesa = self.get_object()
        
        mesa.liberar_mesa()
        return Response({
            'success': True,
            'message': f'Mesa {mesa.numero} liberada',
            'mesa': MesaSerializer(mesa).data
        })

class CentroRequisicaoViewSet(viewsets.ModelViewSet):
    serializer_class = CentroRequisicaoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['ordem_preparo', 'nome']
    
    def get_queryset(self):
        return CentroRequisicao.objects.filter(empresa=self.request.user.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=False)
    def ativos(self, request):
        """Centros ativos"""
        centros = self.get_queryset().filter(ativo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


