# apps/core/views.py
from multiprocessing import context
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta, date
from django.db.models import Count, Sum, F, Q
from apps.analytics.admin import NotificacaoAlertaInline
from apps.analytics.models import EventoAnalytics, NotificacaoAlerta
from apps.clientes.models import Cliente
from apps.core.models import Categoria, Empresa
from apps.estoque.models import MovimentacaoEstoque
from apps.funcionarios.forms import FuncionarioForm
from apps.funcionarios.models import Funcionario
from apps.produtos.models import Produto
from apps.servicos.admin import NotificacaoAgendamentoAdmin
from apps.servicos.models import NotificacaoAgendamento
from apps.vendas.models import FormaPagamento, ItemVenda, Venda
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
import pandas as pd
import openpyxl
from openpyxl import Workbook
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from datetime import datetime
import io
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl import Workbook
from django.db import models
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, F, DecimalField
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView
from apps.vendas.models import Venda
from datetime import date
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin




class BaseMPAView(LoginRequiredMixin, TemplateView):
    """Classe base para todas as views MPA"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user': self.request.user,
            'empresa_atual': self.get_empresa(),
            'current_module': getattr(self, 'module_name', 'dashboard'),
        })
        return context
    
    def get_empresa(self):
        # Esta função já está completa na sua base
        if hasattr(self.request.user, 'usuario') and self.request.user.usuario.empresa:
            return self.request.user.usuario.empresa
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.empresa:
            return self.request.user.profile.empresa
        else:
            try:
                # Importação local para evitar dependência circular
                from apps.core.models import Empresa
                return Empresa.objects.first()
            except ImportError:
                return None


class DashboardView(BaseMPAView):
    template_name = 'core/dashboard.html'
    module_name = 'dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        hoje = timezone.now().date()
        empresa = self.get_empresa()
        
        # Vendas hoje
        try:
            from apps.vendas.models import Venda
            vendas_hoje = Venda.objects.filter(
                empresa=empresa,
                data_venda__date=hoje,
                status='finalizada'
            ).aggregate(
                total=Sum('total'),
                quantidade_atual=Count('id')
            )
        except ImportError:
            vendas_hoje = {'total': 0, 'quantidade': 0}
        
        # Produtos stats
        try:
            from apps.produtos.models import Produto, Categoria
            produtos_stats = {
                'total': Produto.objects.filter(empresa=empresa, ativo=True).count(),
                'total_categorias': Categoria.objects.filter(empresa=empresa, ativa=True).count(),
            }
        except ImportError:
            produtos_stats = {'total': 0, 'total_categorias': 0}
        
        # Estoque stats
        try:
            from apps.produtos.models import Produto
            estoque_stats = {
                'estoque_baixo': Produto.objects.filter(
                    empresa=empresa,
                    ativo=True,
                    estoque_atual__lte=F('estoque_minimo')
                ).count()
            }
        except ImportError:
            estoque_stats = {'estoque_baixo': 0}
        
        
        # Vendas recentes
        try:
            from apps.vendas.models import Venda
            vendas_recentes = Venda.objects.filter(
                empresa=empresa
            ).select_related('cliente').order_by('-data_venda')[:10]
        except ImportError:
            vendas_recentes = []
        
        # =============================================================
        # DADOS DO GRÁFICO DE FATURAMENTO MENSAL
        # =============================================================
        try:
            from apps.vendas.models import Venda
            faturamento_mensal = Venda.objects.filter(
                empresa=empresa,
                status='finalizada'
            ).annotate(
                mes=TruncMonth('data_venda')
            ).values('mes').annotate(
                total_faturamento=Sum('total')
            ).order_by('mes')

            faturamento_labels = [item['mes'].strftime('%Y-%m') for item in faturamento_mensal]
            faturamento_data = [float(item['total_faturamento']) for item in faturamento_mensal]
            
            context['faturamento_labels'] = faturamento_labels
            context['faturamento_data'] = faturamento_data
            
        except (ImportError, TypeError): # Adicionado TypeError para garantir robustez
            context['faturamento_labels'] = []
            context['faturamento_data'] = []
        # =============================================================
        
        context.update({
            'vendas_hoje': vendas_hoje,
            'produtos_stats': produtos_stats,
            'estoque_stats': estoque_stats,
            'vendas_recentes': vendas_recentes,
            'alertas': self.get_alertas(),
        })

        # Exibição apenas para Super Administrador
        if self.request.user.is_superuser:
            # Lista as 10 empresas mais recentes
            try:
                from apps.core.models import Empresa
                from apps.core.models import EventoAnalytics
                lista_empresas = Empresa.objects.all().order_by('-data_cadastro')[:10]
                
                # Lista os 10 últimos acessos (logins) ao sistema
                ultimos_acessos = EventoAnalytics.objects.filter(
                    categoria='usuario',
                    acao='login_sucesso'
                ).select_related('usuario', 'empresa').order_by('-timestamp')[:10]
                
                context['lista_empresas'] = lista_empresas
                context['ultimos_acessos'] = ultimos_acessos
            except ImportError:
                context['lista_empresas'] = []
                context['ultimos_acessos'] = []
        
        return context
    
    def get_alertas(self):
        alertas = []
        empresa = self.get_empresa()
        hoje = timezone.now().date()
        
        # Alertas de estoque baixo
        try:
            from apps.produtos.models import Produto
            produtos_estoque_baixo = Produto.objects.filter(
                empresa=empresa,
                ativo=True,
                estoque_atual__lte=F('estoque_minimo')
            ).count()
            
            if produtos_estoque_baixo > 0:
                alertas.append({
                    'tipo': 'warning',
                    'titulo': 'Estoque Baixo',
                    'mensagem': f'{produtos_estoque_baixo} produtos com estoque baixo',
                    'link': '/dashboard/estoque/',
                    'icone': 'fas fa-exclamation-triangle'
                })
        except ImportError:
            pass
        
        return alertas
    
 





# APIs para AJAX quando necessário
class DashboardStatsAPI(LoginRequiredMixin, View):
    def get(self, request):
        # Retornar stats em JSON para atualizações dinâmicas
        return JsonResponse({'success': True, 'stats': {}})




class CriarCategoriaView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Obter empresa do usuário
            empresa = None
            if hasattr(request.user, 'usuario') and request.user.usuario.empresa:
                empresa = request.user.usuario.empresa
            elif hasattr(request.user, 'profile') and request.user.profile.empresa:
                empresa = request.user.profile.empresa
            else:
                # Fallback: usar primeira empresa ou criar uma de teste
                from apps.core.models import Empresa
                empresa = Empresa.objects.first()
                if not empresa:
                    return JsonResponse({'success': False, 'message': 'Nenhuma empresa encontrada'})
            
            nome = request.POST.get('nome', '').strip()
            codigo = request.POST.get('codigo', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            ativa = request.POST.get('ativa') == 'on'
            
            # Validações
            if not nome:
                return JsonResponse({'success': False, 'message': 'Nome da categoria é obrigatório'})
            
            if len(nome) > 100:
                return JsonResponse({'success': False, 'message': 'Nome muito longo (máximo 100 caracteres)'})
            
            # Verificar se categoria já existe para esta empresa
            if Categoria.objects.filter(nome__iexact=nome, empresa=empresa).exists():
                return JsonResponse({
                    'success': False, 
                    'message': f'Categoria "{nome}" já existe para esta empresa'
                })
            
            # Verificar código se informado
            if codigo and Categoria.objects.filter(codigo__iexact=codigo, empresa=empresa).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Código "{codigo}" já está em uso'
                })
            
            # Criar categoria
            categoria = Categoria.objects.create(
                empresa=empresa,
                nome=nome,
                codigo=codigo if codigo else '',
                descricao=descricao,
                ativa=ativa
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Categoria criada com sucesso',
                'categoria_id': categoria.id,
                'categoria_nome': categoria.nome,
                'categoria_codigo': categoria.codigo
            })
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Erro ao criar categoria: {error_detail}")
            
            return JsonResponse({
                'success': False, 
                'message': f'Erro interno: {str(e)}'
            })
    

class EditarCategoriaView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, categoria_id):
        try:
            empresa = self.get_empresa(request)
            from apps.produtos.models import Categoria
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa)
            
            data = {
                'id': categoria.id,
                'nome': categoria.nome,
                'codigo': categoria.codigo or '',
                'descricao': categoria.descricao or '',
                'ativa': categoria.ativa,
            }
            
            return JsonResponse({'success': True, 'categoria': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def post(self, request, categoria_id):
        try:
            empresa = self.get_empresa(request)
            from apps.produtos.models import Categoria
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa)
            
            nome = request.POST.get('nome', '').strip()
            codigo = request.POST.get('codigo', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            ativa = request.POST.get('ativa') == 'on'
            
            if not nome:
                return JsonResponse({'success': False, 'message': 'Nome da categoria é obrigatório'})
            
            # Verificar se nome já existe em outra categoria
            if Categoria.objects.filter(nome__iexact=nome, empresa=empresa).exclude(id=categoria_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Categoria "{nome}" já existe'
                })
            
            # Verificar código se informado
            if codigo and Categoria.objects.filter(codigo__iexact=codigo, empresa=empresa).exclude(id=categoria_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Código "{codigo}" já está em uso'
                })
            
            # Atualizar categoria
            categoria.nome = nome
            categoria.codigo = codigo
            categoria.descricao = descricao
            categoria.ativa = ativa
            categoria.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Categoria atualizada com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def get_empresa(self, request):
        if hasattr(request.user, 'usuario') and request.user.usuario.empresa:
            return request.user.usuario.empresa
        elif hasattr(request.user, 'profile') and request.user.profile.empresa:
            return request.user.profile.empresa
        else:
            from apps.core.models import Empresa
            return Empresa.objects.first()


class DeletarCategoriaView(LoginRequiredMixin, View):
    def post(self, request, categoria_id):
        try:
            empresa = self.get_empresa(request)
            from apps.produtos.models import Categoria
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa)
            
            # Verificar se há produtos usando esta categoria
            produtos_count = categoria.produtos.count()
            if produtos_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Não é possível remover. Existem {produtos_count} produtos usando esta categoria.'
                })
            
            nome = categoria.nome
            categoria.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Categoria "{nome}" removida com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    def get_empresa(self, request):
        if hasattr(request.user, 'usuario') and request.user.usuario.empresa:
            return request.user.usuario.empresa
        elif hasattr(request.user, 'profile') and request.user.profile.empresa:
            return request.user.profile.empresa
        else:
            from apps.core.models import Empresa
            return Empresa.objects.first()

class ToggleCategoriaView(LoginRequiredMixin, View):
    def post(self, request, categoria_id):
        try:
            # Obter empresa
            empresa = None
            if hasattr(request.user, 'usuario') and request.user.usuario.empresa:
                empresa = request.user.usuario.empresa
            elif hasattr(request.user, 'profile') and request.user.profile.empresa:
                empresa = request.user.profile.empresa
            else:
                from apps.core.models import Empresa
                empresa = Empresa.objects.first()
            
            if not empresa:
                return JsonResponse({'success': False, 'message': 'Empresa não encontrada'})
            
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa)
            
            categoria.ativa = not categoria.ativa
            categoria.save()
            
            return JsonResponse({
                'success': True,
                'ativa': categoria.ativa,
                'message': f'Categoria {"ativada" if categoria.ativa else "desativada"} com sucesso'
            })
            
        except Categoria.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Categoria não encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

from django.views.generic import ListView


class NotificationListView(ListView):
    model = NotificacaoAlerta, NotificacaoAgendamento, NotificacaoAlertaInline
    template_name = "core/notifications_list.html"
    context_object_name = "notifications"



