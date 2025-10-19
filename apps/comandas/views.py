# apps/comandas/views.py
from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import date, timedelta
from .models import Comanda, ItemComanda, CentroRequisicao, TemplateComanda, MovimentacaoComanda
from .serializers import (
    ComandaSerializer, ComandaResumoSerializer, ItemComandaSerializer,
    CentroRequisicaoSerializer, TemplateComandaSerializer
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, FormView, View
)
from .filters import ComandaFilter, MesaFilter
from .models import (
    Comanda, ItemComanda, CentroRequisicao, TemplateComanda, 
    MovimentacaoComanda, ProdutoComanda, CategoriaComanda, 
    Mesa, Pagamento, ConfiguracaoComanda, Comanda, ItemComanda, Mesa, Funcionario
)
from .forms import (
    ComandaForm, ItemComandaForm, MesaForm, OcuparMesaForm, PagamentoForm, ProdutoComandaForm,
    ConfiguracaoComandaForm, CentroRequisicaoForm, ReservarMesaForm, TemplateComandaForm,
    ItemComandaForm, DescontoForm, AcrescimoForm, GorjetaForm, DividirContaForm
)
from django.views.generic import UpdateView, RedirectView
from apps.comandas import models
from django.contrib.auth.mixins import AccessMixin







class PermissaoAcaoMixin(AccessMixin):
    # CRÍTICO: Definir esta variável na View
    acao_requerida = None 

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            # Tenta obter o Funcionario (ligação fundamental)
            funcionario = request.user.funcionario 
        except Exception:
            messages.error(request, "Acesso negado. O seu usuário não está ligado a um registro de funcionário.")
            return self.handle_no_permission()

        if self.acao_requerida:
            # Usa a lógica dinâmica do modelo Funcionario (que já criámos)
            if not funcionario.pode_realizar_acao(self.acao_requerida):
                messages.error(request, f"Acesso negado. O seu cargo não permite realizar a ação de '{self.acao_requerida}'.")
                return redirect(reverse_lazy('core:dashboard'))

        return super().dispatch(request, *args, **kwargs)





class ComandaViewSet(viewsets.ModelViewSet):
    serializer_class = ComandaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComandaFilter
    search_fields = ['numero_comanda', 'descricao', 'solicitante__first_name', 'solicitante__last_name']
    ordering_fields = ['data_solicitacao', 'data_prazo', 'valor_estimado', 'prioridade']
    ordering = ['-data_solicitacao']
    
    def get_queryset(self):
        return Comanda.objects.filter(
            empresa=self.request.user.empresa
        ).select_related(
            'centro_requisicao', 'solicitante', 'atendente', 'aprovador', 'loja'
        ).prefetch_related('itens', 'movimentacoes')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ComandaResumoSerializer
        return ComandaSerializer
    
    def perform_create(self, serializer):
        comanda = serializer.save(
            empresa=self.request.user.empresa,
            solicitante=self.request.user
        )
        
        # Registrar movimentação
        MovimentacaoComanda.objects.create(
            comanda=comanda,
            usuario=self.request.user,
            acao='criada',
            descricao=f"Comanda criada por {self.request.user.get_full_name()}"
        )
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estatísticas para o dashboard de comandas"""
        queryset = self.get_queryset()
        hoje = timezone.now().date()
        
        stats = {
            'comandas_ativas': queryset.filter(
                status__in=['aberta', 'em_andamento', 'parcialmente_atendida']
            ).count(),
            'comandas_pendentes': queryset.filter(status='aberta').count(),
            'comandas_finalizadas_hoje': queryset.filter(
                status='finalizada',
                data_finalizacao__date=hoje
            ).count(),
            'total_hoje': queryset.filter(
                data_solicitacao__date=hoje
            ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0,
            'comandas_atrasadas': self.get_comandas_atrasadas_count(),
            'tempo_medio_atendimento': self.get_tempo_medio_atendimento(),
            'top_solicitantes': self.get_top_solicitantes(),
            'produtos_mais_solicitados': self.get_produtos_mais_solicitados(),
        }
        
        return Response(stats)
    
    def get_comandas_atrasadas_count(self):
        """Conta comandas atrasadas"""
        agora = timezone.now()
        return self.get_queryset().filter(
            status__in=['aberta', 'em_andamento', 'parcialmente_atendida'],
            data_prazo__lt=agora
        ).count()
    
    def get_tempo_medio_atendimento(self):
        """Calcula tempo médio de atendimento em horas"""
        comandas_finalizadas = self.get_queryset().filter(
            status='finalizada',
            data_inicio_atendimento__isnull=False,
            data_finalizacao__isnull=False
        )
        
        if not comandas_finalizadas.exists():
            return 0
        
        tempos = []
        for comanda in comandas_finalizadas:
            delta = comanda.data_finalizacao - comanda.data_inicio_atendimento
            tempos.append(delta.total_seconds() / 3600)
        
        return round(sum(tempos) / len(tempos), 2) if tempos else 0
    
    def get_top_solicitantes(self):
        """Retorna top 5 solicitantes"""
        return list(self.get_queryset().values(
            'solicitante__first_name', 'solicitante__last_name'
        ).annotate(
            total_comandas=Count('id'),
            nome_completo=models.Concat(
                'solicitante__first_name', 
                models.Value(' '), 
                'solicitante__last_name'
            )
        ).order_by('-total_comandas')[:5].values_list('nome_completo', 'total_comandas'))
    
    def get_produtos_mais_solicitados(self):
        """Retorna produtos mais solicitados"""
        from django.db.models import F
        return list(ItemComanda.objects.filter(
            comanda__empresa=self.request.user.empresa,
            comanda__data_solicitacao__gte=timezone.now() - timedelta(days=30)
        ).values('produto__nome_comercial').annotate(
            total_quantidade=Sum('quantidade_solicitada')
        ).order_by('-total_quantidade')[:5].values_list(
            'produto__nome_comercial', 'total_quantidade'
        ))
    
    @action(detail=True, methods=['post'])
    def iniciar_atendimento(self, request, pk=None):
        """Inicia o atendimento de uma comanda"""
        comanda = self.get_object()
        
        if comanda.status != 'aberta':
            return Response(
                {'error': 'Comanda deve estar com status "aberta" para iniciar atendimento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comanda.status = 'em_andamento'
        comanda.atendente = request.user
        comanda.data_inicio_atendimento = timezone.now()
        comanda.save()
        
        # Registrar movimentação
        MovimentacaoComanda.objects.create(
            comanda=comanda,
            usuario=request.user,
            acao='iniciada',
            descricao=f"Atendimento iniciado por {request.user.get_full_name()}"
        )
        
        return Response({'message': 'Atendimento iniciado com sucesso'})
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finaliza uma comanda"""
        comanda = self.get_object()
        
        if comanda.status not in ['em_andamento', 'parcialmente_atendida']:
            return Response(
                {'error': 'Comanda deve estar em andamento para ser finalizada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se há itens pendentes
        itens_pendentes = comanda.itens.filter(
            status__in=['pendente', 'parcial']
        ).count()
        
        if itens_pendentes > 0:
            return Response(
                {'error': f'Existem {itens_pendentes} itens ainda pendentes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comanda.status = 'finalizada'
        comanda.data_finalizacao = timezone.now()
        comanda.observacoes_atendimento = request.data.get('observacoes_finalizacao', '')
        comanda.save()
        
        # Registrar movimentação
        MovimentacaoComanda.objects.create(
            comanda=comanda,
            usuario=request.user,
            acao='finalizada',
            descricao=f"Comanda finalizada por {request.user.get_full_name()}"
        )
        
        return Response({'message': 'Comanda finalizada com sucesso'})
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela uma comanda"""
        comanda = self.get_object()
        
        if comanda.status in ['finalizada', 'cancelada']:
            return Response(
                {'error': 'Não é possível cancelar comanda finalizada ou já cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo', '')
        comanda.status = 'cancelada'
        comanda.observacoes += f"\nCancelada em {timezone.now().date()}: {motivo}"
        comanda.save()
        
        # Registrar movimentação
        MovimentacaoComanda.objects.create(
            comanda=comanda,
            usuario=request.user,
            acao='cancelada',
            descricao=f"Comanda cancelada por {request.user.get_full_name()}. Motivo: {motivo}"
        )
        
        return Response({'message': 'Comanda cancelada com sucesso'})
    
    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """Aprova uma comanda que requer aprovação"""
        comanda = self.get_object()
        
        if not comanda.requer_aprovacao:
            return Response(
                {'error': 'Esta comanda não requer aprovação'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if comanda.aprovada:
            return Response(
                {'error': 'Comanda já foi aprovada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comanda.aprovada = True
        comanda.aprovador = request.user
        comanda.data_aprovacao = timezone.now()
        comanda.save()
        
        # Registrar movimentação
        MovimentacaoComanda.objects.create(
            comanda=comanda,
            usuario=request.user,
            acao='aprovada',
            descricao=f"Comanda aprovada por {request.user.get_full_name()}"
        )
        
        return Response({'message': 'Comanda aprovada com sucesso'})
    
    @action(detail=False, methods=['get'])
    def por_status(self, request):
        """Retorna comandas agrupadas por status"""
        queryset = self.get_queryset()
        
        resultado = {}
        for status_choice in Comanda.STATUS_CHOICES:
            status_key = status_choice[0]
            status_label = status_choice[1]
            
            comandas = queryset.filter(status=status_key)
            serializer = ComandaResumoSerializer(comandas, many=True)
            
            resultado[status_key] = {
                'label': status_label,
                'count': comandas.count(),
                'comandas': serializer.data
            }
        
        return Response(resultado)
    
    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        """Retorna comandas atrasadas"""
        agora = timezone.now()
        comandas_atrasadas = self.get_queryset().filter(
            status__in=['aberta', 'em_andamento', 'parcialmente_atendida'],
            data_prazo__lt=agora
        )
        
        serializer = ComandaResumoSerializer(comandas_atrasadas, many=True)
        return Response(serializer.data)

class ItemComandaViewSet(viewsets.ModelViewSet):
    serializer_class = ItemComandaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ItemComanda.objects.filter(
            comanda__empresa=self.request.user.empresa
        ).select_related('produto', 'lote', 'atendido_por')
    
    @action(detail=True, methods=['post'])
    def atender(self, request, pk=None):
        """Atende um item da comanda"""
        item = self.get_object()
        quantidade_atendida = int(request.data.get('quantidade_atendida', 0))
        lote_id = request.data.get('lote_id')
        observacoes = request.data.get('observacoes', '')
        
        if quantidade_atendida <= 0:
            return Response(
                {'error': 'Quantidade deve ser maior que zero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantidade_atendida > item.saldo_pendente:
            return Response(
                {'error': 'Quantidade não pode ser maior que o saldo pendente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar estoque disponível
        if lote_id:
            from apps.produtos.models import Lote
            try:
                lote = Lote.objects.get(id=lote_id, produto=item.produto)
                if lote.quantidade_atual < quantidade_atendida:
                    return Response(
                        {'error': 'Estoque insuficiente no lote selecionado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item.lote = lote
            except Lote.DoesNotExist:
                return Response(
                    {'error': 'Lote não encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Atualizar item
        item.quantidade_atendida += quantidade_atendida
        item.observacoes_item = observacoes
        item.data_atendimento = timezone.now()
        item.atendido_por = request.user
        item.save()
        
        # Dar baixa no estoque
        if item.lote:
            from apps.estoque.models import MovimentoEstoque
            MovimentoEstoque.objects.create(
                produto=item.produto,
                lote=item.lote,
                tipo_movimento='saida',
                quantidade=quantidade_atendida,
                quantidade_anterior=item.lote.quantidade_atual,
                quantidade_atual=item.lote.quantidade_atual - quantidade_atendida,
                motivo=f"Comanda {item.comanda.numero_comanda}",
                usuario=request.user,
                loja=item.comanda.loja
            )
            
            item.lote.quantidade_atual -= quantidade_atendida
            item.lote.save()
        
        # Registrar movimentação da comanda
        MovimentacaoComanda.objects.create(
            comanda=item.comanda,
            usuario=request.user,
            acao='item_atendido',
            descricao=f"Item {item.produto.nome_comercial} atendido: {quantidade_atendida} {item.unidade_medida}"
        )
        
        # Verificar se comanda pode ser finalizada automaticamente
        if item.comanda.percentual_atendido == 100:
            item.comanda.status = 'finalizada'
            item.comanda.data_finalizacao = timezone.now()
            item.comanda.save()
        
        return Response({'message': 'Item atendido com sucesso'})

class CentroRequisicaoViewSet(viewsets.ModelViewSet):
    serializer_class = CentroRequisicaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CentroRequisicao.objects.filter(empresa=self.request.user.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)

class TemplateComandaViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateComandaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TemplateComanda.objects.filter(
            empresa=self.request.user.empresa
        ).prefetch_related('itens_template__produto')
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)
    
    @action(detail=True, methods=['post'])
    def usar_template(self, request, pk=None):
        """Cria uma nova comanda baseada no template"""
        template = self.get_object()
        loja_id = request.data.get('loja_id')
        
        if not loja_id:
            return Response(
                {'error': 'ID da loja é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.core.models import Loja
            loja = Loja.objects.get(id=loja_id, empresa=request.user.empresa)
        except Loja.DoesNotExist:
            return Response(
                {'error': 'Loja não encontrada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comanda = template.criar_comanda(request.user, loja)
        serializer = ComandaSerializer(comanda)
        
        return Response({
            'message': 'Comanda criada com sucesso a partir do template',
            'comanda': serializer.data
        })


# =====================================
# DASHBOARD E VISÕES GERAIS
# =====================================

class ComandaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'comandas/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa
        hoje = date.today()
        
        # Estatísticas do dia
        comandas_hoje = Comanda.objects.filter(
            empresa=empresa,
            data_abertura__date=hoje
        )
        
        context['estatisticas'] = {
            'comandas_abertas': comandas_hoje.filter(status='aberta').count(),
            'comandas_em_preparo': comandas_hoje.filter(status='em_preparo').count(),
            'comandas_prontas': comandas_hoje.filter(status='pronta').count(),
            'comandas_fechadas': comandas_hoje.filter(status='fechada').count(),
            'faturamento_dia': comandas_hoje.filter(status='fechada').aggregate(
                total=Sum('total')
            )['total'] or 0,
            'ticket_medio': comandas_hoje.filter(status='fechada').aggregate(
                media=Avg('total')
            )['media'] or 0,
        }
        
        # Comandas em andamento
        context['comandas_andamento'] = comandas_hoje.filter(
            status__in=['aberta', 'em_preparo', 'pronta']
        ).select_related('mesa', 'atendente', 'cliente')[:10]
        
        # Mesas ocupadas
        context['mesas_ocupadas'] = Mesa.objects.filter(
            empresa=empresa,
            status='ocupada'
        ).select_related('comanda_set')
        
        # Produtos mais vendidos do dia
        context['produtos_populares'] = ItemComanda.objects.filter(
            comanda__empresa=empresa,
            comanda__data_abertura__date=hoje
        ).values('produto__nome').annotate(
            total_vendido=Sum('quantidade')
        ).order_by('-total_vendido')[:5]
        
        return context

class ComandaListView(LoginRequiredMixin, ListView):
    model = Comanda
    template_name = 'comandas/lista.html'
    context_object_name = 'comandas'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Comanda.objects.filter(
            empresa=self.request.user.empresa
        ).select_related('mesa', 'atendente', 'cliente').order_by('-data_abertura')
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        tipo_atendimento = self.request.GET.get('tipo_atendimento')
        if tipo_atendimento:
            queryset = queryset.filter(tipo_atendimento=tipo_atendimento)
        
        data_inicio = self.request.GET.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(data_abertura__date__gte=data_inicio)
        
        data_fim = self.request.GET.get('data_fim')
        if data_fim:
            queryset = queryset.filter(data_abertura__date__lte=data_fim)
        
        return queryset

# =====================================
# GESTÃO DE COMANDAS
# =====================================

class ComandaCreateView(LoginRequiredMixin, CreateView):
    model = Comanda
    form_class = ComandaForm
    template_name = 'comandas/comanda_form.html'
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        
        # Ocupar mesa se selecionada
        if form.instance.mesa:
            form.instance.mesa.ocupar_mesa()
        
        # Registrar movimentação
        result = super().form_valid(form)
        
        MovimentacaoComanda.registrar_movimentacao(
            comanda=self.object,
            tipo_movimentacao='abertura',
            descricao=f'Comanda aberta por {self.request.user.nome}',
            usuario=self.request.user,
            request=self.request
        )
        
        messages.success(self.request, f'Comanda {self.object.numero_comanda} criada com sucesso!')
        return result
    
    def get_success_url(self):
        return reverse('comandas:detail', kwargs={'pk': self.object.pk})

class ComandaDetailView(LoginRequiredMixin, DetailView):
    model = Comanda
    template_name = 'comandas/comanda_detail.html'
    context_object_name = 'comanda'
    
    def get_queryset(self):
        return Comanda.objects.filter(empresa=self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Itens da comanda
        context['itens'] = self.object.itens.select_related('produto').order_by('hora_pedido')
        
        # Pagamentos
        context['pagamentos'] = self.object.pagamentos.all().order_by('-data_pagamento')
        
        # Movimentações
        context['movimentacoes'] = self.object.movimentacoes.select_related('usuario')[:10]
        
        # Forms para ações
        context['form_item'] = ItemComandaForm(empresa=self.request.user.empresa)
        context['form_pagamento'] = PagamentoForm(
            valor_sugerido=self.object.total - self.object.valor_pago
        )
        
        # Produtos por categoria para modal
        context['categorias'] = CategoriaComanda.objects.filter(
            empresa=self.request.user.empresa,
            ativa=True
        ).prefetch_related('produtocomanda_set')
        
        return context

class AdicionarItemComandaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comanda = get_object_or_404(Comanda, pk=pk, empresa=request.user.empresa)
        
        produto_id = request.POST.get('produto_id')
        quantidade = int(request.POST.get('quantidade', 1))
        observacoes = request.POST.get('observacoes', '')
        
        try:
            produto = ProdutoComanda.objects.get(id=produto_id, empresa=request.user.empresa)
            
            valor_anterior = comanda.total
            comanda.adicionar_item(produto, quantidade, observacoes)
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='adicao_item',
                descricao=f'Adicionado {quantidade}x {produto.nome}',
                usuario=request.user,
                valor_anterior=valor_anterior,
                valor_atual=comanda.total,
                request=request
            )
            
            messages.success(request, f'{quantidade}x {produto.nome} adicionado à comanda')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar item: {str(e)}')
        
        return redirect('comandas:detail', pk=pk)

class RemoverItemComandaView(LoginRequiredMixin, View):
    def post(self, request, pk, item_pk):
        comanda = get_object_or_404(Comanda, pk=pk, empresa=request.user.empresa)
        item = get_object_or_404(ItemComanda, pk=item_pk, comanda=comanda)
        
        if comanda.status not in ['aberta']:
            messages.error(request, 'Não é possível remover itens de comanda fechada')
            return redirect('comandas:detail', pk=pk)
        
        valor_anterior = comanda.total
        produto_nome = item.produto.nome
        quantidade = item.quantidade
        
        # Devolver estoque se necessário
        if item.produto.controla_estoque:
            item.produto.quantidade_estoque += item.quantidade
            item.produto.save()
        
        item.delete()
        comanda.save()  # Recalcular valores
        
        # Registrar movimentação
        MovimentacaoComanda.registrar_movimentacao(
            comanda=comanda,
            tipo_movimentacao='remocao_item',
            descricao=f'Removido {quantidade}x {produto_nome}',
            usuario=request.user,
            valor_anterior=valor_anterior,
            valor_atual=comanda.total,
            request=request
        )
        
        messages.success(request, f'{quantidade}x {produto_nome} removido da comanda')
        return redirect('comandas:detail', pk=pk)

class AdicionarPagamentoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comanda = get_object_or_404(Comanda, pk=pk, empresa=request.user.empresa)
        form = PagamentoForm(request.POST)
        
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.comanda = comanda
            pagamento.save()
            
            # Atualizar valor pago da comanda
            comanda.valor_pago += pagamento.valor
            comanda.save()
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='pagamento',
                descricao=f'Pagamento {pagamento.get_forma_pagamento_display()} - R$ {pagamento.valor}',
                usuario=request.user,
                pagamento_relacionado=pagamento,
                request=request
            )
            
            messages.success(request, f'Pagamento de {pagamento.valor} kz registrado')
            
            # Verificar se comanda foi totalmente paga
            if comanda.valor_pago >= comanda.total:
                comanda.status = 'entregue'
                comanda.save()
                messages.info(request, 'Comanda totalmente paga e marcada como entregue')
        
        else:
            for error in form.errors.values():
                messages.error(request, error)
        
        return redirect('comandas:detail', pk=pk)

class FecharComandaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comanda = get_object_or_404(Comanda, pk=pk, empresa=request.user.empresa)
        
        try:
            comanda.fechar_comanda()
            
            # Registrar movimentação
            MovimentacaoComanda.registrar_movimentacao(
                comanda=comanda,
                tipo_movimentacao='fechamento',
                descricao=f'Comanda fechada por {request.user.nome}',
                usuario=request.user,
                request=request
            )
            
            messages.success(request, f'Comanda {comanda.numero_comanda} fechada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao fechar comanda: {str(e)}')
        
        return redirect('comandas:detail', pk=pk)

# =====================================
# CENTROS DE REQUISIÇÃO (COZINHA)
# =====================================

class CozinhaView(LoginRequiredMixin, TemplateView):
    template_name = 'comandas/cozinha.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa
        
        # Centros de requisição
        centros = CentroRequisicao.objects.filter(
            empresa=empresa,
            ativo=True
        ).order_by('ordem_preparo')
        
        context['centros'] = centros
        
        # Itens pendentes por centro
        itens_por_centro = {}
        for centro in centros:
            itens_pendentes = ItemComanda.objects.filter(
                produto__centro_requisicao=centro,
                status__in=['pendente', 'em_preparo'],
                comanda__empresa=empresa
            ).select_related('comanda', 'produto').order_by('hora_pedido')
            
            itens_por_centro[centro] = itens_pendentes
        
        context['itens_por_centro'] = itens_por_centro
        
        # Estatísticas gerais
        todos_itens_pendentes = ItemComanda.objects.filter(
            comanda__empresa=empresa,
            status__in=['pendente', 'em_preparo']
        )
        
        context['estatisticas'] = {
            'total_pendentes': todos_itens_pendentes.count(),
            'tempo_medio_preparo': todos_itens_pendentes.aggregate(
                media=Avg('produto__tempo_preparo_minutos')
            )['media'] or 0,
        }
        
        return context

class IniciarPreparoItemView(LoginRequiredMixin, View):
    def post(self, request, item_pk):
        item = get_object_or_404(
            ItemComanda, 
            pk=item_pk,
            comanda__empresa=request.user.empresa
        )
        
        try:
            item.iniciar_preparo()
            
            # Atualizar status da comanda se necessário
            if item.comanda.status == 'aberta':
                item.comanda.status = 'em_preparo'
                item.comanda.save()
            
            messages.success(request, f'Preparo iniciado: {item.produto.nome}')
            
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('comandas:cozinha')

class FinalizarPreparoItemView(LoginRequiredMixin, View):
    def post(self, request, item_pk):
        item = get_object_or_404(
            ItemComanda, 
            pk=item_pk,
            comanda__empresa=request.user.empresa
        )
        
        try:
            item.finalizar_preparo()
            
            # Verificar se todos os itens estão prontos
            itens_nao_prontos = item.comanda.itens.exclude(status__in=['pronto', 'entregue'])
            if not itens_nao_prontos.exists():
                item.comanda.status = 'pronta'
                item.comanda.save()
            
            messages.success(request, f'Item finalizado: {item.produto.nome}')
            
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('comandas:cozinha')

# =====================================
# GESTÃO DE PRODUTOS
# =====================================

class ProdutoComandaListView(LoginRequiredMixin, ListView):
    model = ProdutoComanda
    template_name = 'comandas/produto_lista.html'
    context_object_name = 'produtos'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ProdutoComanda.objects.filter(
            empresa=self.request.user.empresa
        ).select_related('categoria').order_by('categoria', 'nome')
        
        # Filtros
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        disponivel = self.request.GET.get('disponivel')
        if disponivel == 'true':
            queryset = queryset.filter(disponivel=True)
        elif disponivel == 'false':
            queryset = queryset.filter(disponivel=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaComanda.objects.filter(
            empresa=self.request.user.empresa
        )
        return context

class ProdutoComandaCreateView(LoginRequiredMixin, CreateView):
    model = ProdutoComanda
    form_class = ProdutoComandaForm
    template_name = 'comandas/produto_form.html'
    success_url = reverse_lazy('comandas:produto_lista')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Produto criado com sucesso!')
        return super().form_valid(form)

# =====================================
# RELATÓRIOS
# =====================================

class RelatoriosView(LoginRequiredMixin, TemplateView):
    template_name = 'comandas/relatorios.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa
        
        # Período para relatório
        data_inicio = self.request.GET.get('data_inicio', date.today().strftime('%Y-%m-%d'))
        data_fim = self.request.GET.get('data_fim', date.today().strftime('%Y-%m-%d'))
        
        comandas = Comanda.objects.filter(
            empresa=empresa,
            data_abertura__date__range=[data_inicio, data_fim]
        )
        
        # Estatísticas gerais
        context['periodo'] = {'inicio': data_inicio, 'fim': data_fim}
        context['total_comandas'] = comandas.count()
        context['comandas_fechadas'] = comandas.filter(status='fechada').count()
        context['faturamento_total'] = comandas.filter(status='fechada').aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Por tipo de atendimento
        context['por_tipo_atendimento'] = comandas.values(
            'tipo_atendimento'
        ).annotate(
            total=Count('id'),
            faturamento=Sum('total')
        ).order_by('-total')
        
        # Produtos mais vendidos
        context['produtos_vendidos'] = ItemComanda.objects.filter(
            comanda__empresa=empresa,
            comanda__data_abertura__date__range=[data_inicio, data_fim]
        ).values('produto__nome').annotate(
            quantidade_total=Sum('quantidade'),
            faturamento=Sum('total')
        ).order_by('-quantidade_total')[:10]
        
        return context

# =====================================
# AJAX E UTILITÁRIOS
# =====================================

class StatusComandaAjaxView(LoginRequiredMixin, View):
    def get(self, request):
        empresa = request.user.empresa
        
        comandas_abertas = Comanda.objects.filter(
            empresa=empresa,
            status__in=['aberta', 'em_preparo', 'pronta']
        ).select_related('mesa').values(
            'id', 'numero_comanda', 'status', 'mesa__numero',
            'total', 'data_abertura'
        )
        
        return JsonResponse({
            'comandas': list(comandas_abertas),
            'timestamp': timezone.now().isoformat()
        })

class ProdutosPorCategoriaAjaxView(LoginRequiredMixin, View):
    def get(self, request):
        categoria_id = request.GET.get('categoria_id')
        
        if not categoria_id:
            return JsonResponse({'produtos': []})
        
        produtos = ProdutoComanda.objects.filter(
            categoria_id=categoria_id,
            empresa=request.user.empresa,
            disponivel=True
        ).values(
            'id', 'nome', 'preco_atual', 'descricao', 'em_promocao'
        )
        
        return JsonResponse({'produtos': list(produtos)})

# =====================================
# VIEWS DE MESAS - ADICIONAR AO ARQUIVO EXISTENTE
# =====================================

class MesaListView(LoginRequiredMixin, ListView):
    model = Mesa
    template_name = 'comandas/mesa_lista.html'
    context_object_name = 'mesas'
    paginate_by = 24
    
    def get_queryset(self):
        queryset = Mesa.objects.filter(
            empresa=self.request.user.empresa
        ).select_related('loja').order_by('numero')
        
        # Aplicar filtros
        filtros = MesaFilter(
            self.request.GET,
            queryset=queryset,
            empresa=self.request.user.empresa
        )
        
        return filtros.qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtros
        context['filtros'] = MesaFilter(
            self.request.GET,
            queryset=self.get_queryset(),
            empresa=self.request.user.empresa
        )
        
        # Estatísticas das mesas
        todas_mesas = Mesa.objects.filter(empresa=self.request.user.empresa)
        context['estatisticas'] = {
            'total_mesas': todas_mesas.count(),
            'mesas_livres': todas_mesas.filter(status='livre', ativa=True).count(),
            'mesas_ocupadas': todas_mesas.filter(status='ocupada').count(),
            'mesas_reservadas': todas_mesas.filter(status='reservada').count(),
            'mesas_limpeza': todas_mesas.filter(status='limpeza').count(),
            'mesas_manutencao': todas_mesas.filter(status='manutencao').count(),
            'mesas_inativas': todas_mesas.filter(ativa=False).count(),
        }
        
        # Taxa de ocupação
        mesas_ativas = todas_mesas.filter(ativa=True).count()
        if mesas_ativas > 0:
            context['estatisticas']['taxa_ocupacao'] = (
                context['estatisticas']['mesas_ocupadas'] / mesas_ativas
            ) * 100
        else:
            context['estatisticas']['taxa_ocupacao'] = 0
        
        # Mesas por status para gráfico
        context['mesas_por_status'] = [
            {'status': 'Livres', 'count': context['estatisticas']['mesas_livres'], 'color': '#28a745'},
            {'status': 'Ocupadas', 'count': context['estatisticas']['mesas_ocupadas'], 'color': '#dc3545'},
            {'status': 'Reservadas', 'count': context['estatisticas']['mesas_reservadas'], 'color': '#ffc107'},
            {'status': 'Limpeza', 'count': context['estatisticas']['mesas_limpeza'], 'color': '#17a2b8'},
            {'status': 'Manutenção', 'count': context['estatisticas']['mesas_manutencao'], 'color': '#6c757d'},
        ]
        
        # Comandas ativas em mesas
        comandas_ativas = Comanda.objects.filter(
            empresa=self.request.user.empresa,
            mesa__isnull=False,
            status__in=['aberta', 'em_preparo', 'pronta']
        ).select_related('mesa').values(
            'mesa__numero', 'numero_comanda', 'status', 'total'
        )
        
        context['comandas_por_mesa'] = {
            comanda['mesa__numero']: comanda for comanda in comandas_ativas
        }
        
        return context

class MesaCreateView(LoginRequiredMixin, CreateView):
    model = Mesa
    form_class = MesaForm
    template_name = 'comandas/mesa_form.html'
    success_url = reverse_lazy('comandas:mesa_lista')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        
        # Definir loja padrão se não especificada
        if not form.instance.loja:
            # Pegar primeira loja da empresa ou loja do usuário
            if hasattr(self.request.user, 'funcionario_profile'):
                funcionario = self.request.user.funcionario_profile
                if funcionario.loja:
                    form.instance.loja = funcionario.loja
            
            if not form.instance.loja:
                primeira_loja = self.request.user.empresa.lojas.first()
                if primeira_loja:
                    form.instance.loja = primeira_loja
        
        messages.success(
            self.request, 
            f'Mesa {form.instance.numero} criada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nova Mesa'
        context['botao_texto'] = 'Criar Mesa'
        return context

class MesaDetailView(LoginRequiredMixin, DetailView):
    model = Mesa
    template_name = 'comandas/mesa_detail.html'
    context_object_name = 'mesa'
    
    def get_queryset(self):
        return Mesa.objects.filter(empresa=self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comanda atual da mesa (se houver)
        comanda_atual = Comanda.objects.filter(
            mesa=self.object,
            status__in=['aberta', 'em_preparo', 'pronta']
        ).select_related('cliente', 'atendente').prefetch_related('itens__produto').first()
        
        context['comanda_atual'] = comanda_atual
        
        # Histórico de comandas desta mesa (últimas 20)
        historico_comandas = Comanda.objects.filter(
            mesa=self.object
        ).select_related('cliente', 'atendente').order_by('-data_abertura')[:20]
        
        context['historico_comandas'] = historico_comandas
        
        # Estatísticas da mesa
        from datetime import date, timedelta
        hoje = date.today()
        data_limite = hoje - timedelta(days=30)  # Últimos 30 dias
        
        comandas_periodo = Comanda.objects.filter(
            mesa=self.object,
            data_abertura__date__gte=data_limite
        )
        
        context['estatisticas_mesa'] = {
            'total_comandas_30_dias': comandas_periodo.count(),
            'faturamento_30_dias': comandas_periodo.filter(
                status='fechada'
            ).aggregate(total=Sum('total'))['total'] or 0,
            'ticket_medio': comandas_periodo.filter(
                status='fechada'
            ).aggregate(media=Avg('total'))['media'] or 0,
            'ocupacao_hoje': Comanda.objects.filter(
                mesa=self.object,
                data_abertura__date=hoje
            ).count(),
        }
        
        # Tempo médio de permanência
        comandas_fechadas = comandas_periodo.filter(
            status='fechada',
            data_fechamento__isnull=False
        )
        
        if comandas_fechadas.exists():
            tempos_permanencia = []
            for comanda in comandas_fechadas:
                tempo = comanda.data_fechamento - comanda.data_abertura
                tempos_permanencia.append(tempo.total_seconds() / 60)  # em minutos
            
            context['estatisticas_mesa']['tempo_medio_permanencia'] = (
                sum(tempos_permanencia) / len(tempos_permanencia)
            )
        else:
            context['estatisticas_mesa']['tempo_medio_permanencia'] = 0
        
        # Forms para ações
        context['form_ocupar'] = OcuparMesaForm()
        context['form_reservar'] = ReservarMesaForm()
        
        return context

class MesaUpdateView(LoginRequiredMixin, UpdateView):
    model = Mesa
    form_class = MesaForm
    template_name = 'comandas/mesa_form.html'
    success_url = reverse_lazy('comandas:mesa_lista')
    
    def get_queryset(self):
        return Mesa.objects.filter(empresa=self.request.user.empresa)
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Mesa {form.instance.numero} atualizada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Mesa {self.object.numero}'
        context['botao_texto'] = 'Salvar Alterações'
        return context

class OcuparMesaView(LoginRequiredMixin, FormView):
    form_class = OcuparMesaForm
    template_name = 'comandas/mesa_ocupar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mesa'] = get_object_or_404(
            Mesa, 
            pk=self.kwargs['pk'], 
            empresa=self.request.user.empresa
        )
        return context
    
    def form_valid(self, form):
        mesa = get_object_or_404(
            Mesa, 
            pk=self.kwargs['pk'], 
            empresa=self.request.user.empresa
        )
        
        # Verificar se mesa pode ser ocupada
        if mesa.status != 'livre':
            messages.error(
                self.request, 
                f'Mesa {mesa.numero} não está livre. Status atual: {mesa.get_status_display()}'
            )
            return redirect('comandas:mesa_detail', pk=mesa.pk)
        
        try:
            # Ocupar mesa
            mesa.ocupar_mesa()
            
            # Criar comanda se solicitado
            criar_comanda = form.cleaned_data.get('criar_comanda', False)
            if criar_comanda:
                cliente = form.cleaned_data.get('cliente')
                atendente = form.cleaned_data.get('atendente') or self.request.user.funcionario_profile
                observacoes = form.cleaned_data.get('observacoes', '')
                
                comanda = Comanda.objects.create(
                    tipo_atendimento='mesa',
                    mesa=mesa,
                    cliente=cliente,
                    atendente=atendente,
                    observacoes=observacoes,
                    empresa=self.request.user.empresa
                )
                
                # Registrar movimentação
                MovimentacaoComanda.registrar_movimentacao(
                    comanda=comanda,
                    tipo_movimentacao='abertura',
                    descricao=f'Comanda criada ao ocupar mesa {mesa.numero}',
                    usuario=self.request.user,
                    request=self.request
                )
                
                messages.success(
                    self.request, 
                    f'Mesa {mesa.numero} ocupada e comanda {comanda.numero_comanda} criada!'
                )
                return redirect('comandas:detail', pk=comanda.pk)
            else:
                messages.success(
                    self.request, 
                    f'Mesa {mesa.numero} ocupada com sucesso!'
                )
                return redirect('comandas:mesa_detail', pk=mesa.pk)
        
        except Exception as e:
            messages.error(self.request, f'Erro ao ocupar mesa: {str(e)}')
            return redirect('comandas:mesa_detail', pk=mesa.pk)

class LiberarMesaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mesa = get_object_or_404(
            Mesa, 
            pk=pk, 
            empresa=request.user.empresa
        )
        
        # Verificar se há comandas abertas na mesa
        comandas_abertas = Comanda.objects.filter(
            mesa=mesa,
            status__in=['aberta', 'em_preparo', 'pronta']
        )
        
        forcar_liberacao = request.POST.get('forcar_liberacao', False)
        
        if comandas_abertas.exists() and not forcar_liberacao:
            messages.error(
                request, 
                f'Mesa {mesa.numero} possui comandas em aberto. '
                'Finalize as comandas antes de liberar a mesa ou force a liberação.'
            )
            return redirect('comandas:mesa_detail', pk=pk)
        
        try:
            # Se forçar liberação, cancelar comandas abertas
            if forcar_liberacao and comandas_abertas.exists():
                for comanda in comandas_abertas:
                    valor_anterior_status = comanda.status
                    comanda.status = 'cancelada'
                    comanda.observacoes += f"\nCancelada automaticamente ao liberar mesa {mesa.numero}"
                    comanda.save()
                    
                    # Registrar movimentação
                    MovimentacaoComanda.registrar_movimentacao(
                        comanda=comanda,
                        tipo_movimentacao='cancelamento',
                        descricao=f'Comanda cancelada ao liberar mesa {mesa.numero}',
                        usuario=request.user,
                        request=request
                    )
            
            # Liberar mesa
            mesa.liberar_mesa()
            
            # Definir novo status se especificado
            novo_status = request.POST.get('novo_status')
            if novo_status and novo_status in dict(Mesa.STATUS_CHOICES):
                mesa.status = novo_status
                mesa.save()
            
            observacoes_liberacao = request.POST.get('observacoes', '')
            if observacoes_liberacao:
                mesa.observacoes += f"\nLiberação: {observacoes_liberacao}"
                mesa.save()
            
            if forcar_liberacao:
                messages.warning(
                    request, 
                    f'Mesa {mesa.numero} liberada forçadamente e comandas canceladas!'
                )
            else:
                messages.success(
                    request, 
                    f'Mesa {mesa.numero} liberada com sucesso!'
                )
        
        except Exception as e:
            messages.error(request, f'Erro ao liberar mesa: {str(e)}')
        
        return redirect('comandas:mesa_detail', pk=pk)

class ReservarMesaView(LoginRequiredMixin, FormView):
    form_class = ReservarMesaForm
    template_name = 'comandas/mesa_reservar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mesa'] = get_object_or_404(
            Mesa, 
            pk=self.kwargs['pk'], 
            empresa=self.request.user.empresa
        )
        return context
    
    def form_valid(self, form):
        mesa = get_object_or_404(
            Mesa, 
            pk=self.kwargs['pk'], 
            empresa=self.request.user.empresa
        )
        
        if mesa.status not in ['livre']:
            messages.error(
                self.request, 
                f'Mesa {mesa.numero} não pode ser reservada. Status atual: {mesa.get_status_display()}'
            )
            return redirect('comandas:mesa_detail', pk=mesa.pk)
        
        try:
            mesa.status = 'reservada'
            
            # Adicionar informações da reserva
            cliente_reserva = form.cleaned_data.get('cliente_reserva', '')
            telefone_reserva = form.cleaned_data.get('telefone_reserva', '')
            observacoes_reserva = form.cleaned_data.get('observacoes_reserva', '')
            
            mesa.observacoes += (
                f"\nReserva: Cliente: {cliente_reserva}, "
                f"Telefone: {telefone_reserva}, "
                f"Obs: {observacoes_reserva}"
            )
            mesa.save()
            
            messages.success(
                self.request, 
                f'Mesa {mesa.numero} reservada para {cliente_reserva}!'
            )
            
        except Exception as e:
            messages.error(self.request, f'Erro ao reservar mesa: {str(e)}')
        
        return redirect('comandas:mesa_detail', pk=mesa.pk)

class MesaDeleteView(LoginRequiredMixin, DeleteView):
    model = Mesa
    template_name = 'comandas/mesa_confirm_delete.html'
    success_url = reverse_lazy('comandas:mesa_lista')
    
    def get_queryset(self):
        return Mesa.objects.filter(empresa=self.request.user.empresa)
    
    def delete(self, request, *args, **kwargs):
        mesa = self.get_object()
        
        # Verificar se mesa pode ser deletada
        if mesa.status == 'ocupada':
            messages.error(request, 'Não é possível deletar mesa ocupada')
            return redirect('comandas:mesa_detail', pk=mesa.pk)
        
        # Verificar se há comandas associadas
        comandas_existentes = Comanda.objects.filter(mesa=mesa).count()
        if comandas_existentes > 0:
            messages.error(
                request, 
                f'Não é possível deletar mesa com {comandas_existentes} comanda(s) associada(s)'
            )
            return redirect('comandas:mesa_detail', pk=mesa.pk)
        
        numero_mesa = mesa.numero
        messages.success(request, f'Mesa {numero_mesa} removida com sucesso!')
        return super().delete(request, *args, **kwargs)

# =====================================
# VIEWS AJAX PARA MESAS
# =====================================

class MesaStatusAjaxView(LoginRequiredMixin, View):
    def get(self, request):
        """Retorna status atual de todas as mesas"""
        mesas = Mesa.objects.filter(
            empresa=request.user.empresa,
            ativa=True
        ).select_related('loja')
        
        dados_mesas = []
        for mesa in mesas:
            # Verificar se há comanda ativa
            comanda_ativa = Comanda.objects.filter(
                mesa=mesa,
                status__in=['aberta', 'em_preparo', 'pronta']
            ).first()
            
            dados_mesas.append({
                'id': mesa.id,
                'numero': mesa.numero,
                'nome': mesa.nome,
                'status': mesa.status,
                'status_display': mesa.get_status_display(),
                'capacidade': mesa.capacidade,
                'localizacao': mesa.localizacao,
                'comanda_ativa': {
                    'numero': comanda_ativa.numero_comanda,
                    'total': float(comanda_ativa.total),
                    'status': comanda_ativa.status,
                } if comanda_ativa else None,
                'qr_code': str(mesa.qr_code),
            })
        
        return JsonResponse({
            'mesas': dados_mesas,
            'timestamp': timezone.now().isoformat()
        })
    
    def post(self, request):
        """Alterar status de uma mesa via AJAX"""
        mesa_id = request.POST.get('mesa_id')
        novo_status = request.POST.get('novo_status')
        
        if not mesa_id or not novo_status:
            return JsonResponse({
                'success': False,
                'message': 'Dados incompletos'
            })
        
        try:
            mesa = Mesa.objects.get(
                id=mesa_id,
                empresa=request.user.empresa
            )
            
            # Validar novo status
            if novo_status not in dict(Mesa.STATUS_CHOICES):
                return JsonResponse({
                    'success': False,
                    'message': 'Status inválido'
                })
            
            # Verificar se alteração é permitida
            if mesa.status == 'ocupada' and novo_status != 'livre':
                # Verificar se há comandas abertas
                comandas_abertas = Comanda.objects.filter(
                    mesa=mesa,
                    status__in=['aberta', 'em_preparo', 'pronta']
                ).exists()
                
                if comandas_abertas:
                    return JsonResponse({
                        'success': False,
                        'message': 'Mesa possui comandas em aberto'
                    })
            
            mesa.status = novo_status
            mesa.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Status da mesa {mesa.numero} alterado para {mesa.get_status_display()}',
                'novo_status': novo_status,
                'novo_status_display': mesa.get_status_display()
            })
            
        except Mesa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Mesa não encontrada'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

class GerarQRCodeMesaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        """Gerar novo QR Code para a mesa"""
        mesa = get_object_or_404(
            Mesa, 
            pk=pk, 
            empresa=request.user.empresa
        )
        
        import uuid
        mesa.qr_code = uuid.uuid4()
        mesa.save()
        
        messages.success(
            request, 
            f'Novo QR Code gerado para mesa {mesa.numero}'
        )
        
        return redirect('comandas:mesa_detail', pk=pk)



# =====================================
# ITENS DA COMANDA
# =====================================

class AdicionarItemView(FormView):
    form_class = ItemComandaForm
    template_name = "comanda/item_form.html"

    def form_valid(self, form):
        comanda = get_object_or_404(Comanda, pk=self.kwargs["comanda_pk"])
        item = form.save(commit=False)
        item.comanda = comanda
        item.save()
        messages.success(self.request, "Item adicionado com sucesso.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class EditarItemView(UpdateView):
    model = ItemComanda
    form_class = ItemComandaForm
    template_name = "comanda/item_form.html"

    def get_success_url(self):
        return reverse_lazy("comanda:detalhe", kwargs={"pk": self.object.comanda.pk})


class RemoverItemView(DeleteView):
    model = ItemComanda
    template_name = "comanda/item_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("comanda:detalhe", kwargs={"pk": self.object.comanda.pk})


class CancelarItemView(View):
    def post(self, request, pk):
        item = get_object_or_404(ItemComanda, pk=pk)
        item.status = "cancelado"
        item.save()
        messages.info(request, "Item cancelado.")
        return redirect("comanda:detalhe", pk=item.comanda.pk)


# =====================================
# OPERAÇÕES FINANCEIRAS
# =====================================

class AplicarDescontoView(FormView):
    form_class = DescontoForm
    template_name = "comanda/operacao_form.html"

    def form_valid(self, form):
        comanda = get_object_or_404(Comanda, pk=self.kwargs["pk"])
        comanda.desconto = form.cleaned_data["valor"]
        comanda.save()
        messages.success(self.request, "Desconto aplicado.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class AplicarAcrescimoView(FormView):
    form_class = AcrescimoForm
    template_name = "comanda/operacao_form.html"

    def form_valid(self, form):
        comanda = get_object_or_404(Comanda, pk=self.kwargs["pk"])
        comanda.acrescimo = form.cleaned_data["valor"]
        comanda.save()
        messages.success(self.request, "Acréscimo aplicado.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class CalcularGorjetaView(FormView):
    form_class = GorjetaForm
    template_name = "comanda/operacao_form.html"

    def form_valid(self, form):
        comanda = get_object_or_404(Comanda, pk=self.kwargs["pk"])
        comanda.gorjeta = form.cleaned_data["percentual"]
        comanda.save()
        messages.success(self.request, "Gorjeta calculada.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class DividirContaView(FormView):
    form_class = DividirContaForm
    template_name = "comanda/operacao_form.html"

    def form_valid(self, form):
        # Implementar lógica de divisão
        messages.success(self.request, "Conta dividida com sucesso.")
        return redirect("comanda:detalhe", pk=self.kwargs["pk"])


# =====================================
# TRANSFERÊNCIAS
# =====================================

class TransferirMesaView(View):
    def post(self, request, pk):
        comanda = get_object_or_404(Comanda, pk=pk)
        nova_mesa_id = request.POST.get("mesa_id")
        comanda.mesa = get_object_or_404(Mesa, pk=nova_mesa_id)
        comanda.save()
        messages.success(request, "Comanda transferida para nova mesa.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class TransferirGarcomView(View):
    def post(self, request, pk):
        comanda = get_object_or_404(Comanda, pk=pk)
        novo_garcom_id = request.POST.get("garcom_id")
        comanda.garcom = get_object_or_404(Funcionario, pk=novo_garcom_id)
        comanda.save()
        messages.success(request, "Comanda transferida para outro garçom.")
        return redirect("comanda:detalhe", pk=comanda.pk)


class TransferirItensView(View):
    def post(self, request):
        itens_ids = request.POST.getlist("itens")
        nova_comanda_id = request.POST.get("comanda_destino")
        nova_comanda = get_object_or_404(Comanda, pk=nova_comanda_id)
        ItemComanda.objects.filter(pk__in=itens_ids).update(comanda=nova_comanda)
        messages.success(request, "Itens transferidos.")
        return redirect("comanda:detalhe", pk=nova_comanda.pk)


# =====================================
# RELATÓRIOS
# =====================================

class ComandaRelatoriosView(TemplateView):
    template_name = "comanda/relatorios.html"


class RelatorioVendasMesaView(TemplateView):
    template_name = "comanda/relatorio_vendas_mesa.html"


class RelatorioTempoAtendimentoView(TemplateView):
    template_name = "comanda/relatorio_tempo.html"


class RelatorioProdutosMaisVendidosView(TemplateView):
    template_name = "comanda/relatorio_produtos.html"


# =====================================
# CONFIGURAÇÕES
# =====================================

class ConfiguracaoComandaView(TemplateView):
    template_name = "comanda/configuracoes.html"


class LayoutMesasView(TemplateView):
    template_name = "comanda/layout_mesas.html"


# =====================================
# IMPRESSÃO
# =====================================

class ImprimirComandaView(DetailView):
    model = Comanda
    template_name = "comanda/imprimir_comanda.html"


class ImprimirContaView(DetailView):
    model = Comanda
    template_name = "comanda/imprimir_conta.html"


class ImprimirCupomView(DetailView):
    model = Comanda
    template_name = "comanda/imprimir_cupom.html"


# =====================================
# AJAX E UTILITÁRIOS
# =====================================

class StatusMesaAjaxView(View):
    def get(self, request):
        mesa_id = request.GET.get("mesa_id")
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        return JsonResponse({"status": mesa.status})


class CalcularTotalAjaxView(View):
    def get(self, request):
        comanda_id = request.GET.get("comanda_id")
        comanda = get_object_or_404(Comanda, pk=comanda_id)
        return JsonResponse({"total": comanda.total})


class BuscarProdutoComandaView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        produtos = ProdutoComanda.objects.filter(nome__icontains=query)[:10]
        data = [{"id": p.id, "nome": p.nome, "preco": str(p.preco)} for p in produtos]
        return JsonResponse(data, safe=False)


class AtualizarMesaAjaxView(View):
    def post(self, request):
        mesa_id = request.POST.get("mesa_id")
        status = request.POST.get("status")
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        mesa.status = status
        mesa.save()
        return JsonResponse({"ok": True, "status": mesa.status})


class MapaMesasView(TemplateView):
    template_name = "comandas/mapa_mesas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mesas"] = Mesa.objects.all().order_by("numero")
        return context



# -------- EDITAR COMANDA --------
class ComandaUpdateView(UpdateView):
    model = Comanda
    form_class = ComandaForm
    template_name = "comandas/comanda_editar.html"
    success_url = reverse_lazy("mapa_mesas")  # redireciona após editar

    def form_valid(self, form):
        messages.success(self.request, "Comanda atualizada com sucesso ✅")
        return super().form_valid(form)


# -------- CANCELAR COMANDA --------
class CancelarComandaView(RedirectView):
    pattern_name = "mapa_mesas"  # volta para o mapa de mesas

    def get_redirect_url(self, *args, **kwargs):
        comanda = Comanda.objects.get(pk=kwargs["pk"])
        comanda.status = Comanda.Status.CANCELADA
        comanda.save()
        messages.warning(self.request, f"Comanda {comanda.id} foi cancelada ❌")
        return super().get_redirect_url(*args, **kwargs)


# -------- REABRIR COMANDA --------
class ReabrirComandaView(RedirectView):
    pattern_name = "mapa_mesas"

    def get_redirect_url(self, *args, **kwargs):
        comanda = Comanda.objects.get(pk=kwargs["pk"])
        comanda.status = Comanda.Status.ABERTA
        comanda.save()
        messages.success(self.request, f"Comanda {comanda.id} foi reaberta 🔄")
        return super().get_redirect_url(*args, **kwargs)



