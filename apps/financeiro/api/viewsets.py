# apps/financeiro/api/viewsets.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from ..models import ContaPagar, ContaReceber, LancamentoFinanceiro, CategoriaFinanceira
from .serializers import ContaPagarSerializer, ContaReceberSerializer, LancamentoFinanceiroSerializer, CategoriaFinanceiraSerializer

class LancamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para Lançamentos Financeiros"""
    
    queryset = LancamentoFinanceiro.objects.all()
    serializer_class = LancamentoFinanceiroSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    filterset_fields = ['tipo', 'criado_por']
    search_fields = ['descricao']
    ordering_fields = ['data', 'valor', 'created_at']
    ordering = ['-data', '-created_at']
    
    def get_queryset(self):
        """Filtrar por empresa do usuário"""
        queryset = super().get_queryset()
        
        # Se usuário tem empresa, filtrar por ela
        if hasattr(self.request.user, 'empresa'):
            # Como LancamentoFinanceiro não tem campo empresa diretamente,
            # vamos filtrar por usuário da mesma empresa
            usuarios_empresa = self.request.user.empresa.funcionarios.values_list('usuario_id', flat=True)
            queryset = queryset.filter(criado_por__in=usuarios_empresa)
        
        return queryset.select_related('criado_por')
    
    def perform_create(self, serializer):
        """Definir usuário criador ao criar lançamento"""
        serializer.save(criado_por=self.request.user)
    
    @action(detail=False, methods=['get'])
    def resumo_periodo(self, request):
        """Retorna resumo financeiro do período"""
        # Parâmetros de data
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio or not data_fim:
            # Padrão: mês atual
            hoje = date.today()
            data_inicio = hoje.replace(day=1)
            ultimo_dia = (data_inicio.replace(month=data_inicio.month + 1) - timedelta(days=1)) if data_inicio.month < 12 else date(data_inicio.year + 1, 1, 1) - timedelta(days=1)
            data_fim = ultimo_dia
        
        # Filtrar lançamentos do período
        queryset = self.get_queryset().filter(
            data__range=[data_inicio, data_fim]
        )
        
        # Calcular totais
        entradas = queryset.filter(tipo='entrada').aggregate(
            total=Sum('valor'),
            quantidade=Count('id')
        )
        
        saidas = queryset.filter(tipo='saida').aggregate(
            total=Sum('valor'),
            quantidade=Count('id')
        )
        
        total_entradas = entradas['total'] or Decimal('0.00')
        total_saidas = saidas['total'] or Decimal('0.00')
        
        # Lançamentos por dia
        lancamentos_por_dia = {}
        for lancamento in queryset.order_by('data'):
            data_str = lancamento.data.strftime('%Y-%m-%d')
            if data_str not in lancamentos_por_dia:
                lancamentos_por_dia[data_str] = {
                    'entradas': Decimal('0.00'),
                    'saidas': Decimal('0.00'),
                    'quantidade': 0
                }
            
            if lancamento.tipo == 'entrada':
                lancamentos_por_dia[data_str]['entradas'] += lancamento.valor
            else:
                lancamentos_por_dia[data_str]['saidas'] += lancamento.valor
            
            lancamentos_por_dia[data_str]['quantidade'] += 1
        
        return Response({
            'periodo': {
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'totais': {
                'entradas': {
                    'valor': total_entradas,
                    'quantidade': entradas['quantidade'] or 0
                },
                'saidas': {
                    'valor': total_saidas,
                    'quantidade': saidas['quantidade'] or 0
                },
                'saldo': total_entradas - total_saidas
            },
            'por_dia': lancamentos_por_dia,
            'media_diaria': {
                'entradas': total_entradas / 30 if total_entradas > 0 else 0,
                'saidas': total_saidas / 30 if total_saidas > 0 else 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Retorna lançamentos agrupados por tipo"""
        # Parâmetros de período
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        queryset = self.get_queryset()
        
        if data_inicio and data_fim:
            queryset = queryset.filter(data__range=[data_inicio, data_fim])
        
        # Agrupar por tipo
        resumo_tipos = queryset.values('tipo').annotate(
            total_valor=Sum('valor'),
            quantidade=Count('id'),
            valor_medio=Avg('valor')
        ).order_by('tipo')
        
        return Response(resumo_tipos)
    
    @action(detail=False, methods=['get'])
    def ultimos_lancamentos(self, request):
        """Retorna últimos lançamentos"""
        limite = int(request.query_params.get('limite', 10))
        
        ultimos = self.get_queryset()[:limite]
        serializer = self.get_serializer(ultimos, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def lancar_lote(self, request):
        """Cria múltiplos lançamentos em lote"""
        lancamentos_data = request.data.get('lancamentos', [])
        
        if not lancamentos_data:
            return Response(
                {'error': 'Lista de lançamentos é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lancamentos_criados = []
        erros = []
        
        for i, dados in enumerate(lancamentos_data):
            try:
                serializer = self.get_serializer(data=dados)
                if serializer.is_valid():
                    lancamento = serializer.save(criado_por=request.user)
                    lancamentos_criados.append(lancamento)
                else:
                    erros.append({
                        'indice': i,
                        'erros': serializer.errors
                    })
            except Exception as e:
                erros.append({
                    'indice': i,
                    'erro': str(e)
                })
        
        return Response({
            'criados': len(lancamentos_criados),
            'erros': len(erros),
            'detalhes_erros': erros,
            'lancamentos': LancamentoFinanceiroSerializer(lancamentos_criados, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def relatorio_mensal(self, request):
        """Relatório mensal detalhado"""
        ano = int(request.query_params.get('ano', date.today().year))
        mes = int(request.query_params.get('mes', date.today().month))
        
        # Período do mês
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
        
        # Lançamentos do mês
        lancamentos_mes = self.get_queryset().filter(
            data__range=[data_inicio, data_fim]
        )
        
        # Estatísticas
        entradas = lancamentos_mes.filter(tipo='entrada')
        saidas = lancamentos_mes.filter(tipo='saida')
        
        total_entradas = entradas.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
        total_saidas = saidas.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
        
        # Maiores lançamentos
        maiores_entradas = entradas.order_by('-valor')[:5]
        maiores_saidas = saidas.order_by('-valor')[:5]
        
        # Lançamentos por usuário
        por_usuario = lancamentos_mes.values(
            'criado_por__nome', 'criado_por__sobrenome'
        ).annotate(
            quantidade=Count('id'),
            total=Sum('valor')
        ).order_by('-total')
        
        return Response({
            'periodo': {
                'ano': ano,
                'mes': mes,
                'data_inicio': data_inicio,
                'data_fim': data_fim
            },
            'resumo': {
                'total_entradas': total_entradas,
                'total_saidas': total_saidas,
                'saldo': total_entradas - total_saidas,
                'quantidade_total': lancamentos_mes.count(),
                'quantidade_entradas': entradas.count(),
                'quantidade_saidas': saidas.count()
            },
            'maiores_lancamentos': {
                'entradas': LancamentoFinanceiroSerializer(maiores_entradas, many=True).data,
                'saidas': LancamentoFinanceiroSerializer(maiores_saidas, many=True).data
            },
            'por_usuario': list(por_usuario)
        })
    
    @action(detail=True, methods=['post'])
    def duplicar(self, request, pk=None):
        """Duplica um lançamento"""
        lancamento_original = self.get_object()
        
        # Dados para o novo lançamento
        nova_data = request.data.get('nova_data', date.today())
        novo_valor = request.data.get('novo_valor', lancamento_original.valor)
        nova_descricao = request.data.get('nova_descricao', f"Cópia de: {lancamento_original.descricao}")
        
        # Criar novo lançamento
        novo_lancamento = LancamentoFinanceiro.objects.create(
            descricao=nova_descricao,
            valor=novo_valor,
            tipo=lancamento_original.tipo,
            data=nova_data,
            criado_por=request.user
        )
        
        serializer = self.get_serializer(novo_lancamento)
        
        return Response({
            'message': 'Lançamento duplicado com sucesso',
            'original': LancamentoFinanceiroSerializer(lancamento_original).data,
            'duplicado': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """Exporta lançamentos para CSV"""
        import csv
        from django.http import HttpResponse
        
        # Filtros
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        tipo = request.query_params.get('tipo')
        
        queryset = self.get_queryset()
        
        if data_inicio and data_fim:
            queryset = queryset.filter(data__range=[data_inicio, data_fim])
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Criar resposta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="lancamentos_{date.today()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data', 'Descrição', 'Tipo', 'Valor', 'Criado Por'])
        
        for lancamento in queryset.order_by('data'):
            writer.writerow([
                lancamento.data.strftime('%d/%m/%Y'),
                lancamento.descricao,
                lancamento.get_tipo_display(),
                float(lancamento.valor),
                lancamento.criado_por.nome if lancamento.criado_por else ''
            ])
        
        return response

class CategoriaFinanceiraViewSet(viewsets.ModelViewSet):
    """ViewSet para Categorias Financeiras"""
    
    queryset = CategoriaFinanceira.objects.all()
    serializer_class = CategoriaFinanceiraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']
    
    def get_queryset(self):
        """Filtrar categorias"""
        queryset = super().get_queryset()
        
        # Adicionar filtros personalizados
        com_descricao = self.request.query_params.get('com_descricao')
        if com_descricao == 'true':
            queryset = queryset.exclude(descricao__isnull=True).exclude(descricao='')
        elif com_descricao == 'false':
            queryset = queryset.filter(Q(descricao__isnull=True) | Q(descricao=''))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas das categorias"""
        queryset = self.get_queryset()
        
        total_categorias = queryset.count()
        com_descricao = queryset.exclude(descricao__isnull=True).exclude(descricao='').count()
        sem_descricao = total_categorias - com_descricao
        
        # Categorias mais usadas (se tivesse relacionamento com lançamentos)
        # Por enquanto, retorna estatísticas básicas
        
        return Response({
            'total_categorias': total_categorias,
            'com_descricao': com_descricao,
            'sem_descricao': sem_descricao,
            'percentual_com_descricao': (com_descricao / total_categorias * 100) if total_categorias > 0 else 0
        })
    
    @action(detail=False, methods=['get'])
    def buscar_por_nome(self, request):
        """Busca categoria por nome (busca inteligente)"""
        nome = request.query_params.get('nome', '').strip()
        
        if not nome:
            return Response({'error': 'Parâmetro nome é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Busca exata
        categoria_exata = self.get_queryset().filter(nome__iexact=nome).first()
        
        if categoria_exata:
            return Response({
                'encontrada': True,
                'tipo': 'exata',
                'categoria': self.get_serializer(categoria_exata).data
            })
        
        # Busca aproximada
        categorias_similares = self.get_queryset().filter(
            nome__icontains=nome
        )[:5]
        
        if categorias_similares.exists():
            return Response({
                'encontrada': True,
                'tipo': 'similar',
                'categorias': self.get_serializer(categorias_similares, many=True).data
            })
        
        # Nenhuma encontrada
        return Response({
            'encontrada': False,
            'sugestao_nome': nome.title()
        })
    
    @action(detail=False, methods=['post'])
    def criar_multiplas(self, request):
        """Cria múltiplas categorias em lote"""
        categorias_data = request.data.get('categorias', [])
        
        if not categorias_data:
            return Response(
                {'error': 'Lista de categorias é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        categorias_criadas = []
        erros = []
        categorias_existentes = []
        
        for i, dados in enumerate(categorias_data):
            nome = dados.get('nome', '').strip()
            
            if not nome:
                erros.append({
                    'indice': i,
                    'erro': 'Nome é obrigatório'
                })
                continue
            
            # Verificar se já existe
            if CategoriaFinanceira.objects.filter(nome__iexact=nome).exists():
                categorias_existentes.append({
                    'indice': i,
                    'nome': nome
                })
                continue
            
            try:
                serializer = self.get_serializer(data=dados)
                if serializer.is_valid():
                    categoria = serializer.save()
                    categorias_criadas.append(categoria)
                else:
                    erros.append({
                        'indice': i,
                        'erros': serializer.errors
                    })
            except Exception as e:
                erros.append({
                    'indice': i,
                    'erro': str(e)
                })
        
        return Response({
            'criadas': len(categorias_criadas),
            'existentes': len(categorias_existentes),
            'erros': len(erros),
            'detalhes': {
                'criadas': CategoriaFinanceiraSerializer(categorias_criadas, many=True).data,
                'existentes': categorias_existentes,
                'erros': erros
            }
        })
    
    @action(detail=True, methods=['get'])
    def uso_categoria(self, request, pk=None):
        """Retorna estatísticas de uso da categoria"""
        categoria = self.get_object()
        
        # Se houvesse relacionamento com lançamentos, calcularia aqui
        # Por enquanto, retorna estrutura básica
        
        return Response({
            'categoria': self.get_serializer(categoria).data,
            'uso': {
                'total_lancamentos': 0,  # Implementar quando houver relacionamento
                'total': 0,
                'ultimo_uso': None,
                'primeiro_uso': None
            },
            'tendencias': {
                'crescimento_mensal': 0,
                'media_valor_lancamento': 0
            }
        })
    
    @action(detail=True, methods=['post'])
    def mesclar_com(self, request, pk=None):
        """Mescla esta categoria com outra"""
        categoria_origem = self.get_object()
        categoria_destino_id = request.data.get('categoria_destino_id')
        
        if not categoria_destino_id:
            return Response(
                {'error': 'ID da categoria destino é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            categoria_destino = CategoriaFinanceira.objects.get(id=categoria_destino_id)
        except CategoriaFinanceira.DoesNotExist:
            return Response(
                {'error': 'Categoria destino não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if categoria_origem.id == categoria_destino.id:
            return Response(
                {'error': 'Não é possível mesclar uma categoria com ela mesma'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aqui mesclaria os lançamentos, se houvesse relacionamento
        # Por enquanto, apenas simula a mesclagem
        
        # Mesclar descrições se necessário
        if categoria_origem.descricao and not categoria_destino.descricao:
            categoria_destino.descricao = categoria_origem.descricao
            categoria_destino.save()
        
        # Salvar informações antes de deletar
        info_origem = {
            'id': categoria_origem.id,
            'nome': categoria_origem.nome,
            'descricao': categoria_origem.descricao
        }
        
        # Deletar categoria origem
        categoria_origem.delete()
        
        return Response({
            'message': 'Categoria mesclada com sucesso',
            'categoria_origem': info_origem,
            'categoria_destino': self.get_serializer(categoria_destino).data,
            'lancamentos_transferidos': 0  # Implementar quando houver relacionamento
        })
    
    @action(detail=False, methods=['get'])
    def exportar_lista(self, request):
        """Exporta lista de categorias"""
        formato = request.query_params.get('formato', 'json')
        
        if formato == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="categorias_{date.today()}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Nome', 'Descrição', 'Data Criação'])
            
            for categoria in self.get_queryset():
                writer.writerow([
                    categoria.id,
                    categoria.nome,
                    categoria.descricao or '',
                    categoria.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(categoria, 'created_at') else ''
                ])
            
            return response
        
        else:  # JSON
            categorias = self.get_queryset()
            serializer = self.get_serializer(categorias, many=True)
            
            return Response({
                'total': categorias.count(),
                'exported_at': timezone.now(),
                'categorias': serializer.data
            })
    
    @action(detail=False, methods=['post'])
    def importar_lista(self, request):
        """Importa lista de categorias"""
        arquivo = request.FILES.get('arquivo')
        
        if not arquivo:
            return Response(
                {'error': 'Arquivo é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Processar arquivo CSV
        if arquivo.name.endswith('.csv'):
            import csv
            import io
            
            # Ler arquivo
            arquivo_string = arquivo.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(arquivo_string))
            
            categorias_criadas = []
            erros = []
            linhas_processadas = 0
            
            for linha in csv_reader:
                linhas_processadas += 1
                nome = linha.get('nome', '').strip()
                descricao = linha.get('descricao', '').strip()
                
                if not nome:
                    erros.append({
                        'linha': linhas_processadas,
                        'erro': 'Nome é obrigatório'
                    })
                    continue
                
                # Verificar se já existe
                if CategoriaFinanceira.objects.filter(nome__iexact=nome).exists():
                    erros.append({
                        'linha': linhas_processadas,
                        'erro': f'Categoria "{nome}" já existe'
                    })
                    continue
                
                try:
                    categoria = CategoriaFinanceira.objects.create(
                        nome=nome,
                        descricao=descricao if descricao else None
                    )
                    categorias_criadas.append(categoria)
                except Exception as e:
                    erros.append({
                        'linha': linhas_processadas,
                        'erro': str(e)
                    })
            
            return Response({
                'processadas': linhas_processadas,
                'criadas': len(categorias_criadas),
                'erros': len(erros),
                'detalhes_erros': erros,
                'categorias_criadas': CategoriaFinanceiraSerializer(categorias_criadas, many=True).data
            })
        
        else:
            return Response(
                {'error': 'Formato de arquivo não suportado. Use CSV.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContaReceberViewSet(viewsets.ModelViewSet):
    queryset = ContaReceber.objects.all()
    serializer_class = ContaReceberSerializer




class ContaPagarViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar Contas a Pagar.
    Permite listar, criar, atualizar e deletar registros.
    """
    queryset = ContaPagar.objects.all()
    serializer_class = ContaPagarSerializer


