# apps/core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.analytics.models import EventoAnalytics, NotificacaoAlerta
from apps.core.models import Categoria, Empresa
from apps.produtos.models import Produto
from apps.vendas.models import Venda
from apps.servicos.models import NotificacaoAgendamento
from datetime import date
import traceback


# ============================================================
# BASE VIEW COM CONTEXTO EMPRESARIAL
# ============================================================
class BaseMPAView(LoginRequiredMixin, TemplateView):
    """View base: define contexto padrão e empresa atual."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user': self.request.user,
            'empresa_atual': self.get_empresa(),
            'current_module': getattr(self, 'module_name', 'dashboard'),
        })
        return context

    def get_empresa(self):
        """Retorna a empresa associada ao usuário logado."""
        user = self.request.user
        if hasattr(user, 'usuario') and user.usuario.empresa:
            return user.usuario.empresa
        elif hasattr(user, 'profile') and user.profile.empresa:
            return user.profile.empresa
        else:
            return Empresa.objects.first()


# ============================================================
# DASHBOARD
# ============================================================
class DashboardView(BaseMPAView):
    template_name = 'core/dashboard.html'
    module_name = 'dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        hoje = timezone.now().date()

        # ======= VENDAS =======
        vendas_hoje = Venda.objects.filter(
            empresa=empresa,
            data_venda__date=hoje,
            status='finalizada'
        ).aggregate(total=Sum('total'), quantidade=Count('id')) or {'total': 0, 'quantidade': 0}

        # ======= PRODUTOS =======
        produtos_stats = {
            'total': Produto.objects.filter(empresa=empresa, ativo=True).count(),
            'total_categorias': Categoria.objects.filter(empresa=empresa, ativa=True).count(),
        }

        # ======= ESTOQUE =======
        estoque_stats = {
            'estoque_baixo': Produto.objects.filter(
                empresa=empresa,
                ativo=True,
                estoque_atual__lte=F('estoque_minimo')
            ).count()
        }

        # ======= VENDAS RECENTES =======
        vendas_recentes = Venda.objects.filter(
            empresa=empresa
        ).select_related('cliente').order_by('-data_venda')[:10]

        # ======= GRÁFICO FATURAMENTO =======
        faturamento_mensal = Venda.objects.filter(
            empresa=empresa,
            status='finalizada'
        ).annotate(
            mes=TruncMonth('data_venda')
        ).values('mes').annotate(
            total_faturamento=Sum('total')
        ).order_by('mes')

        context.update({
            'vendas_hoje': vendas_hoje,
            'produtos_stats': produtos_stats,
            'estoque_stats': estoque_stats,
            'vendas_recentes': vendas_recentes,
            'faturamento_labels': [f["mes"].strftime('%Y-%m') for f in faturamento_mensal],
            'faturamento_data': [float(f["total_faturamento"]) for f in faturamento_mensal],
            'alertas': self.get_alertas(),
        })

        # Exibição adicional para superuser
        if self.request.user.is_superuser:
            context.update({
                'lista_empresas': Empresa.objects.all().order_by('-data_cadastro')[:10],
                'ultimos_acessos': EventoAnalytics.objects.filter(
                    categoria='usuario', acao='login_sucesso'
                ).select_related('usuario', 'empresa').order_by('-timestamp')[:10],
            })

        return context

    def get_alertas(self):
        """Gera lista de alertas (estoque baixo, etc.)"""
        empresa = self.get_empresa()
        produtos_baixo = Produto.objects.filter(
            empresa=empresa, ativo=True, estoque_atual__lte=F('estoque_minimo')
        ).count()
        alertas = []
        if produtos_baixo > 0:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Estoque Baixo',
                'mensagem': f'{produtos_baixo} produtos com estoque baixo',
                'link': '/dashboard/estoque/',
                'icone': 'fas fa-exclamation-triangle'
            })
        return alertas


# ============================================================
# API DASHBOARD (AJAX)
# ============================================================
class DashboardStatsAPI(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({'success': True, 'stats': {}})


# ============================================================
# CRUD DE CATEGORIAS
# ============================================================
@method_decorator(csrf_exempt, name='dispatch')
class CriarCategoriaView(LoginRequiredMixin, View):
    """Cria uma nova categoria vinculada à empresa do usuário."""

    def post(self, request):
        try:
            empresa = self._get_empresa(request)
            nome = request.POST.get('nome', '').strip()
            codigo = request.POST.get('codigo', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            ativa = request.POST.get('ativa') == 'on'

            if not nome:
                return JsonResponse({'success': False, 'message': 'Nome é obrigatório'})

            if Categoria.objects.filter(nome__iexact=nome, empresa=empresa).exists():
                return JsonResponse({'success': False, 'message': 'Categoria já existe'})

            if codigo and Categoria.objects.filter(codigo__iexact=codigo, empresa=empresa).exists():
                return JsonResponse({'success': False, 'message': 'Código já está em uso'})

            categoria = Categoria.objects.create(
                empresa=empresa, nome=nome, codigo=codigo or '', descricao=descricao, ativa=ativa
            )

            return JsonResponse({
                'success': True,
                'message': 'Categoria criada com sucesso',
                'categoria': {'id': categoria.id, 'nome': categoria.nome}
            })

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': str(e)})

    def _get_empresa(self, request):
        user = request.user
        if hasattr(user, 'usuario') and user.usuario.empresa:
            return user.usuario.empresa
        elif hasattr(user, 'profile') and user.profile.empresa:
            return user.profile.empresa
        return Empresa.objects.first()


@method_decorator(csrf_exempt, name='dispatch')
class EditarCategoriaView(LoginRequiredMixin, View):
    """Edita categoria de forma segura por empresa."""

    def post(self, request, categoria_id):
        empresa = self._get_empresa(request)
        categoria = get_object_or_404(Categoria, id=categoria_id, empresa=empresa)

        nome = request.POST.get('nome', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        ativa = request.POST.get('ativa') == 'on'

        if not nome:
            return JsonResponse({'success': False, 'message': 'Nome é obrigatório'})

        if Categoria.objects.filter(nome__iexact=nome, empresa=empresa).exclude(id=categoria.id).exists():
            return JsonResponse({'success': False, 'message': 'Categoria já existe'})

        categoria.nome = nome
        categoria.codigo = codigo
        categoria.descricao = descricao
        categoria.ativa = ativa
        categoria.save()

        return JsonResponse({'success': True, 'message': 'Categoria atualizada com sucesso'})

    def _get_empresa(self, request):
        user = request.user
        if hasattr(user, 'usuario') and user.usuario.empresa:
            return user.usuario.empresa
        elif hasattr(user, 'profile') and user.profile.empresa:
            return user.profile.empresa
        return Empresa.objects.first()


class DeletarCategoriaView(LoginRequiredMixin, View):
    """Remove categoria apenas se não houver produtos associados."""

    def post(self, request, categoria_id):
        empresa = self._get_empresa(request)
        categoria = get_object_or_404(Categoria, id=categoria_id, empresa=empresa)

        if categoria.produtos.exists():
            return JsonResponse({
                'success': False,
                'message': 'Não é possível remover: há produtos associados.'
            })

        nome = categoria.nome
        categoria.delete()
        return JsonResponse({'success': True, 'message': f'Categoria "{nome}" removida com sucesso'})

    def _get_empresa(self, request):
        user = request.user
        if hasattr(user, 'usuario') and user.usuario.empresa:
            return user.usuario.empresa
        elif hasattr(user, 'profile') and user.profile.empresa:
            return user.profile.empresa
        return Empresa.objects.first()


class ToggleCategoriaView(LoginRequiredMixin, View):
    """Ativa/Desativa categoria restrita à empresa."""

    def post(self, request, categoria_id):
        empresa = self._get_empresa(request)
        categoria = get_object_or_404(Categoria, id=categoria_id, empresa=empresa)

        categoria.ativa = not categoria.ativa
        categoria.save()

        return JsonResponse({
            'success': True,
            'ativa': categoria.ativa,
            'message': f'Categoria {"ativada" if categoria.ativa else "desativada"} com sucesso'
        })

    def _get_empresa(self, request):
        user = request.user
        if hasattr(user, 'usuario') and user.usuario.empresa:
            return user.usuario.empresa
        elif hasattr(user, 'profile') and user.profile.empresa:
            return user.profile.empresa
        return Empresa.objects.first()


# ============================================================
# LISTAGEM DE NOTIFICAÇÕES
# ============================================================
class NotificationListView(LoginRequiredMixin, ListView):
    """Lista todas as notificações (alertas e agendamentos)."""
    template_name = "core/notifications_list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        empresa = self.request.user.usuario.empresa if hasattr(self.request.user, 'usuario') else None
        return NotificacaoAlerta.objects.filter(empresa=empresa).order_by('-id')

