# apps/vendas/views.py
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import decimal
import json
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.core.cache import caches
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from requests import Response, request
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from apps.configuracoes.models import DadosBancarios, PersonalizacaoInterface
from apps.core.utils import gerar_qr_fatura
from apps.core.views import BaseMPAView
from apps.financeiro.models import ContaBancaria, MovimentoCaixa
from apps.funcionarios.models import Funcionario
from apps.produtos.models import Produto
from apps.servicos.models import Servico
from apps.vendas.api.serializers import ItemVendaSerializer, VendaSerializer
from datetime import timedelta
from .models import (
    Comissao, Convenio, Entrega, Orcamento, ItemOrcamento, Venda, ItemVenda, PagamentoVenda,
    DevolucaoVenda, ItemDevolucao, FormaPagamento
)
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import (
     VendaForm, PagamentoVendaForm,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count
from django.views.generic import TemplateView, ListView, DetailView, View
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from decimal import Decimal
from apps.vendas.models import Venda, ItemVenda, FormaPagamento
from apps.produtos.models import Produto
from apps.funcionarios.models import Funcionario
from apps.core.models import Empresa # Importa Empresa da app core
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import *
from .forms import *
from apps.clientes.models import Cliente, EnderecoCliente, Ponto
from apps.produtos.models import Produto
from apps.funcionarios.models import Funcionario
from apps.servicos.models import Servico
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string
from weasyprint import HTML
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.db.models import Prefetch
from weasyprint import HTML, CSS
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from .models import FaturaCredito, Recibo 
from apps.core.services import gerar_numero_documento

from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required

from django.db import transaction
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string

from weasyprint import HTML, CSS # Exemplo com WeasyPrint (recomendado)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Venda, FaturaCredito, Recibo, FaturaProforma
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
from django.db.models import Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.response import Response
from django.db import transaction
from .tasks import verificar_margem_critica # Importe a tarefa Celery
from django.core.cache import caches
from .models import (
    Venda, NotaCredito, ItemNotaCredito, NotaDebito,
    ItemNotaDebito, DocumentoTransporte, ItemDocumentoTransporte
)
from .forms import (
    NotaCreditoForm, ItemNotaCreditoForm, NotaDebitoForm, ItemNotaDebitoForm,
    DocumentoTransporteForm, ItemDocumentoTransporteForm
)
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import logging


from apps.vendas.models import FaturaCredito, Recibo, FormaPagamento 
from apps.financeiro.models import MovimentacaoFinanceira, PlanoContas
from apps.financeiro.models import ContaBancaria
from django.contrib.auth.decorators import permission_required

logger = logging.getLogger(__name__)

import logging
import traceback
from django.db import transaction
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages


class BaseVendaView(LoginRequiredMixin):
    """View base para o módulo de vendas"""
    
    def get_empresa(self):
        """Retorna a empresa do usuário logado"""
        return self.request.user.empresa

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
                return redirect(reverse_lazy('core:dashboard')) # Redirecionamento para a Home ou Dashboard

        return super().dispatch(request, *args, **kwargs)


class VendasView(BaseMPAView):
    template_name = 'vendas/vendas.html'
    module_name = 'vendas'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        empresa = self.get_empresa()
        hoje = timezone.now().date()
        
        # Filtros do GET
        periodo = self.request.GET.get('periodo', 'mes')
        status = self.request.GET.get('status', '')
        vendedor_id = self.request.GET.get('vendedor', '')
        cliente_nome = self.request.GET.get('cliente', '')
        valor_min = self.request.GET.get('valor_min', '')
        sort = self.request.GET.get('sort', '-data_venda')
        
        # Query base
        vendas = Venda.objects.filter(empresa=empresa)
        
        # Aplicar filtros de período
        if periodo == 'hoje':
            vendas = vendas.filter(data_venda__date=hoje)
        elif periodo == 'semana':
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            vendas = vendas.filter(data_venda__date__gte=inicio_semana)
        elif periodo == 'mes':
            vendas = vendas.filter(
                data_venda__year=hoje.year,
                data_venda__month=hoje.month
            )
        elif periodo == 'trimestre':
            inicio_trimestre = hoje.replace(month=((hoje.month - 1) // 3) * 3 + 1, day=1)
            vendas = vendas.filter(data_venda__date__gte=inicio_trimestre)
        
        # Outros filtros
        if status:
            vendas = vendas.filter(status=status)
        
        if vendedor_id:
            vendas = vendas.filter(vendedor_id=vendedor_id)
        
        if cliente_nome:
            vendas = vendas.filter(
                Q(cliente__nome_completo__icontains=cliente_nome) |
                Q(cliente__cpf__icontains=cliente_nome)
            )
        
        if valor_min:
            try:
                vendas = vendas.filter(total__gte=float(valor_min))
            except ValueError:
                pass
        
        # Ordenação
        if sort.startswith('-'):
            vendas = vendas.order_by(sort)
        else:
            vendas = vendas.order_by(sort)
        
        # Paginação
        paginator = Paginator(vendas, self.paginate_by)
        page_number = self.request.GET.get('page')
        vendas_page = paginator.get_page(page_number)
        
        # Stats
        vendas_mes = Venda.objects.filter(
            empresa=empresa,
            data_venda__year=hoje.year,
            data_venda__month=hoje.month,
            status='finalizada'
        ).aggregate(
            total=Sum('total'),
            quantidade=Count('id')
        )
        
        # Vendedores para filtro
        vendedores = []
        try:
            from apps.funcionarios.models import Funcionario
            vendedores = Funcionario.objects.filter(
                empresa=empresa,
                ativo=True
            ).values('id', 'nome_completo')
        except:
            pass
        
        # Total das vendas filtradas
        vendas_total = vendas.aggregate(total=Sum('total'))['total'] or 0
        
        context.update({
            'vendas': vendas_page,
            'vendas_total': vendas_total,
            'vendas_stats': {
                'vendas_mes': float(vendas_mes['total'] or 0),
                'quantidade_mes': vendas_mes['quantidade'] or 0,
                'ticket_medio': float(vendas_mes['total'] or 0) / max(vendas_mes['quantidade'] or 1, 1),
                'clientes_mes': vendas.filter(
                    data_venda__year=hoje.year,
                    data_venda__month=hoje.month
                ).values('cliente').distinct().count(),
                'crescimento_mes': 12.5,  # Calcular crescimento real
                'vendas_hoje': vendas.filter(data_venda__date=hoje).count(),
                'variacao_ticket': 5.2,  # Calcular variação real
                'novos_clientes': 15,  # Calcular novos clientes
            },
            'vendedores': vendedores,
            'paginator': paginator,
            'is_paginated': vendas_page.has_other_pages(),
            'page_obj': vendas_page,
        })
        
        return context

class VendaDetailView(DetailView):
    """
    Exibe os detalhes de uma venda, incluindo itens e eventual orçamento de origem.
    """
    model = Venda
    template_name = "vendas/venda_detail.html"
    context_object_name = "venda"

    def get_queryset(self):
        """
        Garante que só retorne vendas da empresa do usuário logado.
        Assim evita acesso de uma empresa a outra.
        """
        empresa = self.request.user.empresa if hasattr(self.request.user, "empresa") else None
        return Venda.objects.filter(empresa=empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda = self.get_object()

        # Itens da venda
        context["itens"] = venda.itens.all()

        # Orçamento de origem, se existir
        context["orcamento_origem"] = getattr(venda, "orcamento_origem", None)

        # Pode adicionar estatísticas locais (ex: margem, desconto médio etc.)
        context["resumo"] = {
            "subtotal": sum([i.valor_unitario * i.quantidade for i in venda.itens.all()]),
            "desconto_total": sum([i.desconto if hasattr(i, "desconto") else 0 for i in venda.itens.all()]),
            "criada_em": venda.data_venda,
            "status": venda.status,
        }

        return context

class BaseVendaView(LoginRequiredMixin):
    """Classe base para views de vendas"""
    
    def get_empresa(self):
        if hasattr(self.request.user, 'funcionario'):
            return self.request.user.funcionario.empresa
        return None
    
    def get_queryset(self):
        empresa = self.get_empresa()
        if empresa:
            return super().get_queryset().filter(empresa=empresa)
        return super().get_queryset().none()

class VendaCreateView(PermissaoAcaoMixin, BaseVendaView, CreateView):
    # 💥 NOVA LINHA DE SEGURANÇA
    acao_requerida = 'vender'

    model = Venda
    form_class = VendaForm
    template_name = 'vendas/venda_form.html'
    success_url = reverse_lazy('vendas:lista')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        form.instance.vendedor = self.request.user.funcionario
        form.instance.usuario_criacao = self.request.user
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Gerar número da venda
            if not form.instance.numero_venda:
                form.instance.numero_venda = f"V{form.instance.id:06d}"
                form.instance.save()
            
            messages.success(self.request, f'Venda {form.instance.numero_venda} criada com sucesso!')
            return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        context.update({
            'title': 'Nova Venda',
            'clientes': Cliente.objects.filter(empresa=empresa, ativo=True),
            'produtos': Produto.objects.filter(empresa=empresa, ativo=True),
            'formas_pagamento': FormaPagamento.objects.filter(empresa=empresa, ativa=True),
        })
        return context

class VendaDetailView(BaseVendaView, DetailView):
    model = Venda
    template_name = 'vendas/venda_detail.html'
    context_object_name = 'venda'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda = self.get_object()
        
        context.update({
            'title': f'Venda {venda.numero_venda}',
            'itens': venda.itens.select_related('produto'),
            'pagamentos': venda.pagamentos.all(),
            'pode_editar': venda.status in ['rascunho', 'pendente'],
            'pode_cancelar': venda.status in ['pendente', 'finalizada'],
        })
        return context

class VendaUpdateView(BaseVendaView, UpdateView):
    model = Venda
    form_class = VendaForm
    template_name = 'vendas/venda_form.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        if self.object.status not in ['rascunho', 'pendente']:
            messages.error(self.request, 'Não é possível editar esta venda.')
            return redirect(self.get_success_url())
        
        form.instance.usuario_modificacao = self.request.user
        messages.success(self.request, 'Venda atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        context.update({
            'title': f'Editar Venda {self.object.numero_venda}',
            'clientes': Cliente.objects.filter(empresa=empresa, ativo=True),
            'produtos': Produto.objects.filter(empresa=empresa, ativo=True),
            'formas_pagamento': FormaPagamento.objects.filter(empresa=empresa, ativa=True),
        })
        return context

class CancelarVendaView(BaseVendaView, View):
    # 💥 NOVA LINHA DE SEGURANÇA
    acao_requerida = 'cancelar_venda'
    
    def post(self, request, pk):
        venda = get_object_or_404(Venda, pk=pk, empresa=self.get_empresa())
        
        if venda.status == 'cancelada':
            messages.warning(request, 'Venda já está cancelada.')
        
        if venda.total > Decimal('1000') and not self.request.user.funcionario.pode_realizar_acao('cancelar_venda_alto_valor'):
             messages.error(request, "Cancelações de alto valor requerem autorização superior.")
             return redirect('vendas:detail', pk=pk)
        
        elif venda.status not in ['pendente', 'finalizada']:
            messages.error(request, 'Não é possível cancelar esta venda.')
        else:
            with transaction.atomic():
                # Reverter estoque
                for item in venda.itens.all():
                    produto = item.produto
                    produto.estoque_atual += item.quantidade
                    produto.save()
                
                # Cancelar venda
                venda.status = 'cancelada'
                venda.data_cancelamento = timezone.now()
                venda.motivo_cancelamento = request.POST.get('motivo', 'Cancelamento solicitado')
                venda.usuario_cancelamento = request.user
                venda.save()
                
                messages.success(request, f'Venda {venda.numero_venda} cancelada com sucesso!')
        
        return redirect('vendas:detail', pk=pk)

class OrcamentoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Orcamento
    template_name = "vendas/orcamento_list.html"
    context_object_name = "orcamentos"
    permission_required = "vendas.view_orcamento"
    paginate_by = 20

    def get_queryset(self):
        # Filtrar apenas orçamentos da empresa do usuário logado
        return Orcamento.objects.filter(empresa=self.request.user.empresa)

class OrcamentoDetailView(DetailView):
    model = Orcamento
    template_name = "orcamentos/orcamento_detail.html"
    context_object_name = "orcamento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orcamento = self.get_object()
        context["itens"] = orcamento.itens.all()
        context["pode_converter"] = (orcamento.status == "aprovado")
        return context

def converter_orcamento_em_venda(request, pk):
    """
    Converte um orçamento aprovado em venda.
    """
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if orcamento.status != "aprovado":
        messages.error(request, "Somente orçamentos aprovados podem ser convertidos em venda.")
        return redirect("orcamentos:orcamento_detail", pk=orcamento.pk)

    if orcamento.venda_convertida:
        messages.warning(request, "Este orçamento já foi convertido em uma venda.")
        return redirect("orcamentos:orcamento_detail", pk=orcamento.pk)

    # Criar a venda a partir do orçamento
    venda = Venda.objects.create(
        empresa=orcamento.empresa,
        cliente=orcamento.cliente,
        vendedor=orcamento.vendedor,
        data_venda=timezone.now(),
        total=orcamento.total,
        observacoes=f"Venda originada do orçamento {orcamento.numero_orcamento}"
    )

    # Converter itens do orçamento para itens de venda
    for item in orcamento.itens.all():
        venda.itens.create(
            produto=item.produto,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            total=item.total,
        )

    # Atualizar status do orçamento
    orcamento.status = "convertido"
    orcamento.venda_convertida = venda
    orcamento.save()

    messages.success(request, f"Orçamento {orcamento.numero_orcamento} convertido em venda {venda.id}.")
    return redirect("vendas:venda_detail", pk=venda.pk)

class OrcamentoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Orcamento
    template_name = "vendas/orcamento_form.html"
    fields = [
        "numero_orcamento",
        "cliente",
        "data_validade",
        "valor_subtotal",
        "valor_desconto",
        "total",
        "status",
        "observacoes",
    ]
    permission_required = "vendas.add_orcamento"
    success_url = reverse_lazy("vendas:orcamento_lista")

    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        form.instance.vendedor = self.request.user
        return super().form_valid(form)

class OrcamentoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Orcamento
    template_name = "vendas/orcamento_form.html"
    fields = [
        "cliente",
        "data_validade",
        "valor_subtotal",
        "valor_desconto",
        "total",
        "status",
        "observacoes",
    ]
    permission_required = "vendas.change_orcamento"
    success_url = reverse_lazy("vendas:orcamento_lista")

class OrcamentoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Orcamento
    template_name = "vendas/orcamento_confirm_delete.html"
    permission_required = "vendas.delete_orcamento"
    success_url = reverse_lazy("vendas:orcamento_lista")

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from django.utils import timezone

from .models import Orcamento, ItemOrcamento, Venda, ItemVenda

class VendaDashboardView(BaseVendaView, TemplateView):
    template_name = 'vendas/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        hoje = timezone.now().date()
        mes_atual = hoje.replace(day=1)
        
        # Vendas hoje
        vendas_hoje = Venda.objects.filter(
            empresa=empresa,
            data_venda__date=hoje,
            status='finalizada'
        ).aggregate(
            total=Sum('total'),
            quantidade=Count('id')
        )
        
        # Vendas do mês
        vendas_mes = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=mes_atual,
            status='finalizada'
        ).aggregate(
            total=Sum('total'),
            quantidade=Count('id')
        )
        
        # Top produtos
        top_produtos = ItemVenda.objects.filter(
            venda__empresa=empresa,
            venda__data_venda__gte=mes_atual,
            venda__status='finalizada'
        ).values(
            'produto__nome_comercial'
        ).annotate(
            quantidade_vendida=Sum('quantidade'),
            total=Sum('total')
        ).order_by('-quantidade_vendida')[:10]
        
        # Vendas por forma de pagamento
        vendas_por_pagamento = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=mes_atual,
            status='finalizada'
        ).values('forma_pagamento__nome').annotate(
            total=Sum('total'),
            quantidade=Count('id')
        )
        
        context.update({
            'title': 'Dashboard de Vendas',
            'vendas_hoje': vendas_hoje,
            'vendas_mes': vendas_mes,
            'top_produtos': top_produtos,
            'vendas_por_pagamento': vendas_por_pagamento,
        })
        return context

class OrcamentoConverterView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "vendas.add_venda"

    def post(self, request, pk):
        orcamento = get_object_or_404(Orcamento, pk=pk, empresa=request.user.empresa)

        if orcamento.status in ["convertido", "cancelado", "expirado"]:
            messages.error(request, "Este orçamento não pode ser convertido.")
            return redirect("vendas:orcamento_detail", pk=orcamento.pk)

        # Criar a venda com base no orçamento
        venda = Venda.objects.create(
            empresa=orcamento.empresa,
            cliente=orcamento.cliente,
            vendedor=request.user,
            data_venda=timezone.now(),
            valor_subtotal=orcamento.valor_subtotal,
            valor_desconto=orcamento.valor_desconto,
            total=orcamento.total,
            status="concluida",  # ou o status inicial que você usa
            observacoes=f"Venda originada do orçamento #{orcamento.numero_orcamento}",
        )

        # Copiar os itens
        for item in orcamento.itens.all():
            ItemVenda.objects.create(
                venda=venda,
                produto=item.produto,
                quantidade=item.quantidade,
                valor_unitario=item.valor_unitario,
                total=item.total,
            )

        # Atualizar orçamento
        orcamento.status = "convertido"
        orcamento.venda_convertida = venda
        orcamento.save()

        messages.success(request, f"Orçamento {orcamento.numero_orcamento} convertido em venda {venda.id}.")
        return redirect("vendas:detail", pk=venda.pk)

class OrcamentoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Orcamento
    template_name = "vendas/orcamento_list.html"
    context_object_name = "orcamentos"
    paginate_by = 20
    permission_required = "vendas.view_orcamento"

    def get_queryset(self):
        qs = Orcamento.objects.filter(empresa=self.request.user.empresa).select_related("cliente", "vendedor")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

class PagamentoListView(BaseVendaView, ListView):
    model = PagamentoVenda
    template_name = 'vendas/pagamento_lista.html'
    context_object_name = 'pagamentos'
    
    def get_queryset(self):
        venda_pk = self.kwargs.get('venda_pk')
        return PagamentoVenda.objects.filter(
            venda__pk=venda_pk,
            venda__empresa=self.get_empresa()
        ).order_by('-data_pagamento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda_pk = self.kwargs.get('venda_pk')
        venda = get_object_or_404(Venda, pk=venda_pk, empresa=self.get_empresa())
        
        context.update({
            'venda': venda,
            'title': f'Pagamentos - Venda {venda.numero_venda}',
        })
        return context

class PagamentoCreateView(BaseVendaView, CreateView):
    model = PagamentoVenda
    form_class = PagamentoVendaForm
    template_name = 'vendas/pagamento_form.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:pagamento_lista', kwargs={'venda_pk': self.kwargs.get('venda_pk')})
    
    def form_valid(self, form):
        venda_pk = self.kwargs.get('venda_pk')
        venda = get_object_or_404(Venda, pk=venda_pk, empresa=self.get_empresa())
        
        form.instance.venda = venda
        form.instance.usuario_criacao = self.request.user
        
        messages.success(self.request, 'Pagamento registrado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda_pk = self.kwargs.get('venda_pk')
        venda = get_object_or_404(Venda, pk=venda_pk, empresa=self.get_empresa())
        
        context.update({
            'venda': venda,
            'title': f'Novo Pagamento - Venda {venda.numero_venda}',
        })
        return context

class PagamentoDetailView(BaseVendaView, DetailView):
    model = PagamentoVenda
    template_name = 'vendas/pagamento_detail.html'
    context_object_name = 'pagamento'
    
    def get_queryset(self):
        return PagamentoVenda.objects.filter(venda__empresa=self.get_empresa())



from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from django.views import View


class EstornarPagamentoView(PermissaoAcaoMixin, BaseVendaView, View):
    # 🚨 PONTO CRÍTICO DE SEGURANÇA: Ação que será verificada no Cargo
    acao_requerida = 'estornar_pagamento' 

    def post(self, request, pk):
        # O PermissaoAcaoMixin já tratou o bloqueio se a permissão for False.
        
        pagamento = get_object_or_404(PagamentoVenda, pk=pk, venda__empresa=self.get_empresa())
        
        # ⚠️ Verificação Adicional de Segurança: Status do Pagamento
        if pagamento.status == 'estornado':
            messages.warning(request, 'O pagamento já está marcado como estornado. Nenhuma ação foi executada.')
        else:
            # 🔄 Transação Atómica: Tudo ou nada. Fundamental para finanças.
            try:
                with transaction.atomic():
                    # 1. Atualização do Objeto Pagamento
                    pagamento.status = 'estornado'
                    pagamento.data_estorno = timezone.now()
                    
                    # Usa o usuário logado para auditoria (quem fez o estorno)
                    pagamento.usuario_estorno = request.user 
                    
                    # Pega o motivo do estorno, geralmente de um campo POST oculto
                    pagamento.motivo_estorno = request.POST.get('motivo', 'Estorno via sistema (motivo não especificado)')
                    pagamento.save()

                    # 3. Atualizar o status da Venda (se a venda estava totalmente paga)
                    pagamento.venda.calcular_saldo_e_atualizar_status() # Método que você deve ter ou criar na Venda
                    
                    messages.success(request, f'Pagamento de R$ {pagamento.valor_pago} estornado com sucesso. Verifique o impacto no Caixa/Contas.')
            except Exception as e:
                # O rollback da transação será automático.
                messages.error(request, f'Falha crítica ao estornar pagamento. Transação revertida. Erro: {e}')
                # Logar este erro é mandatório para sistemas financeiros.
                logger.error(f"Erro no estorno de PagamentoVenda {pk}: {e}", exc_info=True)
                
        return redirect('vendas:pagamento_detail', pk=pk)



class PagamentoCartaoView(BaseVendaView, TemplateView):
    template_name = 'vendas/pagamento_cartao.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pagamento Cartão'
        return context

class PagamentoConvenioView(BaseVendaView, TemplateView):
    template_name = 'vendas/pagamento_convenio.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pagamento Convênio'
        return context

class PagamentoCrediarioView(BaseVendaView, TemplateView):
    template_name = 'vendas/pagamento_crediario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pagamento Crediário'
        return context

# =====================================
# DEVOLUÇÕES E TROCAS
# =====================================

class DevolucaoListView(BaseVendaView, ListView):
    model = DevolucaoVenda
    template_name = 'vendas/devolucao_lista.html'
    context_object_name = 'devolucoes'
    paginate_by = 20
    
    def get_queryset(self):
        return DevolucaoVenda.objects.filter(
            venda__empresa=self.get_empresa()
        ).select_related('venda', 'cliente').order_by('-data_devolucao')


class DevolucaoVendaView(BaseVendaView, CreateView):
    acao_requerida = 'fazer_devolucao'

    model = DevolucaoVenda
    form_class = DevolucaoForm
    template_name = 'vendas/devolucao_form.html'
    success_url = reverse_lazy('vendas:devolucao_lista')
    
    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get('pk')
        venda = get_object_or_404(Venda, pk=pk, empresa=self.get_empresa())
        initial['venda'] = venda
        initial['cliente'] = venda.cliente
        return initial
    
    def form_valid(self, form):
        form.instance.usuario_criacao = self.request.user
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Processar devolução dos itens
            devolucao = form.instance
            for item_dev in devolucao.itens.all():
                produto = item_dev.produto
                produto.estoque_atual += item_dev.quantidade
                produto.save()
            
            messages.success(self.request, f'Devolução registrada com sucesso!')
            return response


class DevolucaoDetailView(BaseVendaView, DetailView):
    model = DevolucaoVenda
    template_name = 'vendas/devolucao_detail.html'
    context_object_name = 'devolucao'
    
    def get_queryset(self):
        return DevolucaoVenda.objects.filter(venda__empresa=self.get_empresa())

class DeliveryListView(BaseVendaView, ListView):
    model = Venda
    template_name = 'vendas/delivery_lista.html'
    context_object_name = 'vendas'
    paginate_by = 20
    
    def get_queryset(self):
        return Venda.objects.filter(
            empresa=self.get_empresa(),
            tipo_venda='delivery'
        ).select_related('cliente').order_by('-data_venda')

class AgendarEntregaView(BaseVendaView, UpdateView):
    model = Venda
    form_class = AgendarEntregaForm
    template_name = 'vendas/agendar_entrega.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.status_entrega = 'agendada'
        messages.success(self.request, 'Entrega agendada com sucesso!')
        return super().form_valid(form)


class EntregaListView(BaseVendaView, ListView):
    model = Entrega
    template_name = 'vendas/entrega_lista.html'
    context_object_name = 'entregas'
    paginate_by = 20
    
    def get_queryset(self):
        return Entrega.objects.filter(
            venda__empresa=self.get_empresa()
        ).select_related('venda', 'entregador').order_by('-data_agendada')


class ConfirmarEntregaView(BaseVendaView, View):
    def post(self, request, pk):
        entrega = get_object_or_404(Entrega, pk=pk, venda__empresa=self.get_empresa())
        
        entrega.status = 'entregue'
        entrega.data_entrega = timezone.now()
        entrega.confirmado_por = request.user
        entrega.observacoes_entrega = request.POST.get('observacoes', '')
        entrega.save()
        
        # Atualizar status da venda
        entrega.venda.status_entrega = 'entregue'
        entrega.venda.save()
        
        messages.success(request, 'Entrega confirmada com sucesso!')
        return redirect('vendas:entrega_lista')


class RotaEntregaView(BaseVendaView, TemplateView):
    template_name = 'vendas/rota_entrega.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        
        entregas_hoje = Entrega.objects.filter(
            venda__empresa=self.get_empresa(),
            data_agendada__date=hoje,
            status__in=['agendada', 'saiu_entrega']
        ).select_related('venda', 'entregador')
        
        context.update({
            'title': 'Rota de Entrega',
            'entregas_hoje': entregas_hoje,
        })
        return context


# =====================================
# CONVÊNIOS E PARCERIAS
# =====================================

class ConvenioListView(BaseVendaView, ListView):
    model = Convenio
    template_name = 'vendas/convenio_lista.html'
    context_object_name = 'convenios'
    paginate_by = 20
    
    def get_queryset(self):
        return Convenio.objects.filter(
            empresa=self.get_empresa()
        ).order_by('nome')


class ConvenioCreateView(BaseVendaView, CreateView):
    model = Convenio
    form_class = ConvenioForm
    template_name = 'vendas/convenio_form.html'
    success_url = reverse_lazy('vendas:convenio_lista')
    
    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        messages.success(self.request, 'Convênio cadastrado com sucesso!')
        return super().form_valid(form)


class ConvenioDetailView(BaseVendaView, DetailView):
    model = Convenio
    template_name = 'vendas/convenio_detail.html'
    context_object_name = 'convenio'
    
    def get_queryset(self):
        return Convenio.objects.filter(empresa=self.get_empresa())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        convenio = self.get_object()
        
        # Vendas do convênio
        vendas = Venda.objects.filter(
            convenio=convenio,
            empresa=self.get_empresa()
        ).order_by('-data_venda')[:10]
        
        context.update({
            'vendas_recentes': vendas,
        })
        return context


class FaturarConvenioView(BaseVendaView, TemplateView):
    template_name = 'vendas/faturar_convenio.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        convenio = get_object_or_404(Convenio, pk=pk, empresa=self.get_empresa())
        
        # Vendas pendentes de faturamento
        vendas_pendentes = Venda.objects.filter(
            convenio=convenio,
            empresa=self.get_empresa(),
            status_faturamento='pendente'
        )
        
        context.update({
            'convenio': convenio,
            'vendas_pendentes': vendas_pendentes,
            'total_faturar': vendas_pendentes.aggregate(Sum('total'))['total__sum'] or 0,
        })
        return context





# =====================================
# DASHBOARDS E ANALYTICS
# =====================================


class VendaAnalyticsView(BaseVendaView, TemplateView):
    template_name = 'vendas/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Período para análise
        periodo = self.request.GET.get('periodo', '30')
        data_inicio = timezone.now().date() - timedelta(days=int(periodo))
        
        # Vendas por dia
        vendas_por_dia = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=data_inicio,
            status='finalizada'
        ).extra(
            select={'dia': 'date(data_venda)'}
        ).values('dia').annotate(
            total=Sum('total'),
            quantidade=Count('id')
        ).order_by('dia')
        
        # Vendas por vendedor
        vendas_por_vendedor = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=data_inicio,
            status='finalizada'
        ).values(
            'vendedor__nome_completo'
        ).annotate(
            total=Sum('total'),
            quantidade=Count('id')
        ).order_by('-total')
        
        # Ticket médio
        ticket_medio = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=data_inicio,
            status='finalizada'
        ).aggregate(Avg('total'))['total__avg'] or 0
        
        context.update({
            'title': 'Analytics de Vendas',
            'vendas_por_dia': vendas_por_dia,
            'vendas_por_vendedor': vendas_por_vendedor,
            'ticket_medio': ticket_medio,
            'periodo': periodo,
        })
        return context


class VendaKPIsView(BaseVendaView, TemplateView):
    template_name = 'vendas/kpis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        hoje = timezone.now().date()
        mes_atual = hoje.replace(day=1)
        mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
        
        # KPIs do mês atual
        kpis_atual = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=mes_atual,
            status='finalizada'
        ).aggregate(
            faturamento=Sum('total'),
            quantidade_vendas=Count('id'),
            ticket_medio=Avg('total')
        )
        
        # KPIs do mês anterior
        kpis_anterior = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=mes_anterior,
            data_venda__lt=mes_atual,
            status='finalizada'
        ).aggregate(
            faturamento=Sum('total'),
            quantidade_vendas=Count('id'),
            ticket_medio=Avg('total')
        )
        
        # Calcular crescimento
        def calcular_crescimento(atual, anterior):
            if anterior and anterior > 0:
                return ((atual - anterior) / anterior) * 100
            return 0 if atual == 0 else 100
        
        crescimento_faturamento = calcular_crescimento(
            kpis_atual['faturamento'] or 0,
            kpis_anterior['faturamento'] or 0
        )
        
        crescimento_vendas = calcular_crescimento(
            kpis_atual['quantidade_vendas'] or 0,
            kpis_anterior['quantidade_vendas'] or 0
        )
        
        context.update({
            'title': 'KPIs de Vendas',
            'kpis_atual': kpis_atual,
            'kpis_anterior': kpis_anterior,
            'crescimento_faturamento': crescimento_faturamento,
            'crescimento_vendas': crescimento_vendas,
        })
        return context


class MetasVendaView(BaseVendaView, TemplateView):
    template_name = 'vendas/metas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        hoje = timezone.now().date()
        mes_atual = hoje.replace(day=1)
        
        # Buscar metas do mês
        try:
            meta_mes = MetaVenda.objects.get(
                empresa=empresa,
                mes=mes_atual.month,
                ano=mes_atual.year
            )
        except MetaVenda.DoesNotExist:
            meta_mes = None
        
        # Vendas realizadas no mês
        vendas_mes = Venda.objects.filter(
            empresa=empresa,
            data_venda__gte=mes_atual,
            status='finalizada'
        ).aggregate(
            total_vendido=Sum('total'),
            quantidade_vendas=Count('id')
        )
        
        # Calcular percentual de atingimento
        percentual_faturamento = 0
        percentual_quantidade = 0
        
        if meta_mes:
            if meta_mes.meta_faturamento > 0:
                percentual_faturamento = (vendas_mes['total_vendido'] or 0) / meta_mes.meta_faturamento * 100
            
            if meta_mes.meta_quantidade > 0:
                percentual_quantidade = (vendas_mes['quantidade_vendas'] or 0) / meta_mes.meta_quantidade * 100
        
        context.update({
            'title': 'Metas de Vendas',
            'meta_mes': meta_mes,
            'vendas_mes': vendas_mes,
            'percentual_faturamento': percentual_faturamento,
            'percentual_quantidade': percentual_quantidade,
        })
        return context


# =====================================
# COMISSÕES
# =====================================

class ComissaoListView(BaseVendaView, ListView):
    model = Comissao
    template_name = 'vendas/comissao_lista.html'
    context_object_name = 'comissoes'
    paginate_by = 20
    
    def get_queryset(self):
        return Comissao.objects.filter(
            vendedor__empresa=self.get_empresa()
        ).select_related('vendedor', 'venda').order_by('-data_venda')


class CalcularComissaoView(BaseVendaView, TemplateView):
    template_name = 'vendas/calcular_comissao.html'
    
    def post(self, request):
        mes = int(request.POST.get('mes'))
        ano = int(request.POST.get('ano'))
        vendedor_id = request.POST.get('vendedor_id')
        
        # Filtros
        vendas = Venda.objects.filter(
            empresa=self.get_empresa(),
            data_venda__month=mes,
            data_venda__year=ano,
            status='finalizada'
        )
        
        if vendedor_id:
            vendas = vendas.filter(vendedor_id=vendedor_id)
        
        # Calcular comissões
        for venda in vendas:
            Comissao.calcular_comissao(venda)
        
        messages.success(request, 'Comissões calculadas com sucesso!')
        return redirect('vendas:comissao_lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Calcular Comissões',
            'vendedores': Funcionario.objects.filter(
                empresa=self.get_empresa(),
                ativo=True
            ),
        })
        return context


class PagarComissaoView(BaseVendaView, View):
    def post(self, request):
        comissao_ids = request.POST.getlist('comissao_ids')
        
        with transaction.atomic():
            comissoes = Comissao.objects.filter(
                id__in=comissao_ids,
                vendedor__empresa=self.get_empresa(),
                status='calculada'
            )
            
            for comissao in comissoes:
                comissao.status = 'paga'
                comissao.data_pagamento = timezone.now()
                comissao.save()
        
        messages.success(request, f'{len(comissoes)} comissões pagas com sucesso!')
        return redirect('vendas:comissao_lista')


# =====================================
# AJAX E UTILITÁRIOS
# =====================================

class CalcularDescontoView(BaseVendaView, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            subtotal = Decimal(str(data.get('subtotal', 0)))
            desconto_valor = Decimal(str(data.get('desconto_valor', 0)))
            desconto_tipo = data.get('desconto_tipo', 'valor')
            
            if desconto_tipo == 'percentual':
                valor_desconto = subtotal * (desconto_valor / 100)
            else:
                valor_desconto = desconto_valor
            
            total = subtotal - valor_desconto
            
            return JsonResponse({
                'success': True,
                'valor_desconto': float(valor_desconto),
                'total': float(total)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class VerificarEstoqueVendaView(BaseVendaView, View):
    def get(self, request):
        produto_id = request.GET.get('produto_id')
        quantidade = int(request.GET.get('quantidade', 1))
        
        try:
            produto = Produto.objects.get(
                id=produto_id,
                empresa=self.get_empresa()
            )
            
            disponivel = produto.estoque_atual >= quantidade
            
            return JsonResponse({
                'disponivel': disponivel,
                'estoque_atual': produto.estoque_atual,
                'quantidade_solicitada': quantidade
            })
        except Produto.DoesNotExist:
            return JsonResponse({
                'disponivel': False,
                'error': 'Produto não encontrado'
            })


class CalcularTrocoView(BaseVendaView, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            total = Decimal(str(data.get('total', 0)))
            valor_recebido = Decimal(str(data.get('valor_recebido', 0)))
            
            troco = valor_recebido - total
            
            return JsonResponse({
                'success': True,
                'troco': float(troco)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


# =====================================
# API REST
# =====================================

class CancelarVendaAPIView(BaseVendaView, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            venda_id = data.get('venda_id')
            motivo = data.get('motivo', 'Cancelamento via API')
            
            venda = get_object_or_404(Venda, id=venda_id, empresa=self.get_empresa())
            
            if venda.status == 'cancelada':
                return JsonResponse({
                    'success': False,
                    'message': 'Venda já está cancelada'
                })
            
            with transaction.atomic():
                # Reverter estoque
                for item in venda.itens.all():
                    produto = item.produto
                    produto.estoque_atual += item.quantidade
                    produto.save()
                
                # Cancelar venda
                venda.status = 'cancelada'
                venda.data_cancelamento = timezone.now()
                venda.motivo_cancelamento = motivo
                venda.usuario_cancelamento = request.user
                venda.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Venda {venda.numero_venda} cancelada com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


class ConsultarPrecoAPIView(BaseVendaView, View):
    def get(self, request):
        produto_id = request.GET.get('produto_id')
        quantidade = int(request.GET.get('quantidade', 1))
        
        try:
            produto = Produto.objects.get(
                id=produto_id,
                empresa=self.get_empresa()
            )
            
            preco_unitario = produto.preco_venda
            subtotal = preco_unitario * quantidade
            
            # Verificar promoções ou descontos especiais aqui
            desconto = Decimal('0.00')
            total = subtotal - desconto
            
            return JsonResponse({
                'success': True,
                'produto': {
                    'id': produto.id,
                    'nome': produto.nome_comercial,
                    'preco_unitario': float(preco_unitario),
                    'quantidade': quantidade,
                    'subtotal': float(subtotal),
                    'desconto': float(desconto),
                    'total': float(total)
                }
            })
            
        except Produto.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Produto não encontrado'
            })


class AplicarDescontoAPIView(BaseVendaView, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            venda_id = data.get('venda_id')
            desconto_valor = Decimal(str(data.get('desconto_valor', 0)))
            desconto_tipo = data.get('desconto_tipo', 'valor')
            
            venda = get_object_or_404(Venda, id=venda_id, empresa=self.get_empresa())
            
            if venda.status not in ['rascunho', 'pendente']:
                return JsonResponse({
                    'success': False,
                    'message': 'Não é possível aplicar desconto nesta venda'
                })
            
            # Calcular desconto
            if desconto_tipo == 'percentual':
                valor_desconto = venda.subtotal * (desconto_valor / 100)
            else:
                valor_desconto = desconto_valor
            
            # Aplicar desconto
            venda.valor_desconto = valor_desconto
            venda.calcular_totais()
            venda.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Desconto aplicado com sucesso',
                'venda': {
                    'subtotal': float(venda.subtotal),
                    'desconto': float(venda.valor_desconto),
                    'total': float(venda.total)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })




from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.vendas.models import Venda, ItemVenda, FormaPagamento
from apps.clientes.models import Cliente
from apps.produtos.models import Produto




# apps/vendas/views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

# Importe os seus modelos e serializers
from apps.vendas.models import Venda, ItemVenda, FormaPagamento
from apps.produtos.models import Produto
from apps.clientes.models import Cliente
from apps.funcionarios.models import Funcionario
from .api.serializers import RentabilidadeItemSerializer, VendaSerializer, ItemVendaSerializer

class PDVView(LoginRequiredMixin, TemplateView):
    """
    Renderiza o template do PDV com os dados iniciais.
    Esta view só responde a requisições GET.
    """
    template_name = 'vendas/pdv.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Lógica para obter a empresa do usuário
        empresa = self.request.user.empresa if hasattr(self.request.user, 'empresa') else None
        
        context.update({
            'clientes': list(Cliente.objects.filter(empresa=empresa, ativo=True).values('id', 'nome_completo')),
            'produtos': list(Produto.objects.filter(empresa=empresa, ativo=True).values('id', 'nome_produto', 'preco_venda', 'estoque_atual')),
            'formas_pagamento': list(FormaPagamento.objects.filter(empresa=empresa, ativa=True).values('id', 'nome')),
        })
        return context

class PDVCreateAPIView(APIView):
    """
    View de API para criação de uma venda completa (PDV).
    Processa a venda e seus itens de forma atômica.
    Esta view só responde a requisições POST.
    """
    def post(self, request, *args, **kwargs):
        # O código que você forneceu aqui está correto para a API
        # ... manter o código da sua views.PDVCreateAPIView aqui ...
        with transaction.atomic():
            venda_data = request.data.get('venda')
            itens_data = request.data.get('itens')

            if not itens_data:
                return Response({'detail': 'A venda deve conter pelo menos um item.'}, status=status.HTTP_400_BAD_REQUEST)

            # 1. Serializar e validar os dados da Venda
            venda_serializer = VendaSerializer(data=venda_data)
            if venda_serializer.is_valid():
                # Forçar o status para 'finalizada' no PDV
                venda_serializer.validated_data['status'] = 'finalizada'
                venda = venda_serializer.save()

                # 2. Serializar e validar os dados dos itens da venda
                for item_data in itens_data:
                    item_data['venda'] = venda.id  # Vincula o item à venda recém-criada
                    item_serializer = ItemVendaSerializer(data=item_data)

                    if item_serializer.is_valid():
                        item_serializer.save()
                        # Lógica de atualização de estoque
                        produto = item_serializer.validated_data['produto']
                        produto.estoque_atual -= item_serializer.validated_data['quantidade']
                        produto.save()
                    else:
                        raise ValueError(f"Dados do item inválidos: {item_serializer.errors}")

                return Response(VendaSerializer(venda).data, status=status.HTTP_201_CREATED)
            else:
                return Response(venda_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalvarRascunhoApiView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            import json
            data = json.loads(request.body)
            
            empresa = self.get_empresa(request)
            
            # Criar venda como rascunho
            from apps.vendas.models import Venda, ItemVenda
            
            venda = Venda.objects.create(
                empresa=empresa,
                usuario=request.user,
                cliente_id=data.get('cliente_id'),
                forma_pagamento=data.get('forma_pagamento', 'dinheiro'),
                valor_desconto=data.get('desconto', 0),
                observacoes=data.get('observacoes', ''),
                status='rascunho'
            )
            
            # Adicionar itens
            total = 0
            for item_data in data.get('itens', []):
                from apps.produtos.models import Produto
                produto = Produto.objects.get(id=item_data['produto_id'], empresa=empresa)
                
                item = ItemVenda.objects.create(
                    venda=venda,
                    produto=produto,
                    quantidade=item_data['quantidade'],
                    preco_unitario=item_data['preco_unitario']
                )
                
                total += item.quantidade * item.preco_unitario
            
            # Atualizar valor total da venda
            venda.total = total - venda.valor_desconto
            venda.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Rascunho salvo com sucesso',
                'venda_id': venda.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao salvar rascunho: {str(e)}'
            })
    
    def get_empresa(self, request):
        if hasattr(request.user, 'usuario') and request.user.usuario.empresa:
            return request.user.usuario.empresa
        elif hasattr(request.user, 'profile') and request.user.profile.empresa:
            return request.user.profile.empresa
        else:
            from apps.core.models import Empresa
            return Empresa.objects.first()


class AbrirGavetaApiView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Log da abertura da gaveta
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Gaveta aberta por: {request.user.username}')
            
            # Aqui você pode adicionar integração com hardware específico
            # Por exemplo, enviar comando para impressora fiscal
            
            return JsonResponse({
                'success': True,
                'message': 'Gaveta aberta com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao abrir gaveta: {str(e)}'
            })






import json
from django.db import transaction, models
from django.http import JsonResponse
from apps.clientes.models import Cliente
from apps.produtos.models import Produto
from .models import Venda, ItemVenda, FormaPagamento, PagamentoVenda
from decimal import Decimal
import logging
from django.utils import timezone
from django.db.models import F

logger = logging.getLogger(__name__)


def to_decimal(value):
    """
    Converte um valor (string ou numérico) para um objeto Decimal de forma segura.
    Retorna Decimal('0.00') se o valor for inválido.
    """
    if value is None or value == "":
        return Decimal('0.00')
    
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
        
    value_str = str(value).strip()
    
    try:
        # Substitui a vírgula por ponto para o separador decimal
        # E remove separadores de milhar (apenas se houver ambos)
        if ',' in value_str and '.' in value_str:
            if value_str.index('.') < value_str.index(','):
                value_str = value_str.replace('.', '')
        
        return Decimal(value_str.replace(',', '.'))
    except (ValueError, TypeError, decimal.InvalidOperation):
        logger.error(f"Erro de conversão para Decimal no valor: {value}")
        return Decimal('0.00')

def to_int(value):
    return int(value)


def finalizar_venda_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Utilizador não autenticado.'}, status=401)

    try:
        funcionario = request.user.funcionario
        if not funcionario.pode_realizar_acao('vender'):
            # Permissão de cargo negada!
            return JsonResponse({'success': False, 'message': 'O seu cargo não permite finalizar vendas.'}, status=403)
        
        data = json.loads(request.body)
        
        required_fields = ['itens', 'forma_pagamento_id', 'total_pago']
        if not all(field in data for field in required_fields):
            return JsonResponse({'success': False, 'message': 'Campo(s) obrigatório(s) ausente(s).'}, status=400)

        itens_venda = data.get('itens', [])
        if not itens_venda:
            return JsonResponse({'success': False, 'message': 'O carrinho está vazio.'}, status=400)

        with transaction.atomic():
            funcionario = request.user.funcionario
            loja = funcionario.loja_principal
            empresa = loja.empresa
            cliente = Cliente.objects.filter(id=data.get('cliente_id')).first()
            forma_pagamento = FormaPagamento.objects.get(id=data['forma_pagamento_id'])
            valor_pago_decimal = to_decimal(data['total_pago'])

            subtotal_final = Decimal('0.00')
            desconto_final = Decimal('0.00')
            iva_final = Decimal('0.00')
            total_final = Decimal('0.00')
            
            itens_processados = []

            print("Etapa 1: Pré-processamento e cálculos. Iniciando o loop.")

            # 1. PRÉ-PROCESSAMENTO E CÁLCULOS
            for item in itens_venda:
                produto_id = item.get('produto_id')
                servico_id = item.get('servico_id')
                quantidade = to_int(item.get('quantidade', 0))

                if produto_id:
                    # Processa Produto
                    if quantidade <= 0:
                        raise ValueError(f"Quantidade inválida para o produto de ID {produto_id}")
                    try:
                        produto = Produto.objects.get(id=produto_id)
                    except Produto.DoesNotExist:
                        raise ValueError(f"Produto com ID {produto_id} não encontrado.")

                    if quantidade > produto.estoque_atual:
                        raise ValueError(f"Estoque insuficiente para o produto: {produto.nome_produto}")

                    preco_unitario = to_decimal(item.get('preco_unitario', produto.preco_venda))
                    desconto_item = to_decimal(item.get('desconto_item', "0.00"))

                    subtotal_item = (preco_unitario * quantidade) - desconto_item
                    iva_item = subtotal_item * (produto.iva_percentual / Decimal('100.00'))
                    total_item = subtotal_item + iva_item

                    subtotal_final += subtotal_item
                    desconto_final += desconto_item
                    iva_final += iva_item
                    total_final += total_item
                    
                    itens_processados.append({
                        'tipo': 'produto',
                        'produto_obj': produto,
                        'quantidade': quantidade,
                        'preco_unitario': preco_unitario,
                        'desconto_item': desconto_item,
                        'subtotal_item': subtotal_item,
                        'iva_percentual': produto.iva_percentual,
                        'iva_valor': iva_item,
                        'total_item': total_item
                    })
                    print(f"Item processado (produto). ID: {produto_id}, Quantidade: {quantidade}")

                elif servico_id:
                    # Processa Serviço
                    if quantidade <= 0:
                        raise ValueError(f"Quantidade inválida para o serviço de ID {servico_id}")
                    try:
                        servico = Servico.objects.get(id=servico_id)
                    except Servico.DoesNotExist:
                        raise ValueError(f"Serviço com ID {servico_id} não encontrado.")

                    preco_unitario = to_decimal(item.get('preco_unitario', servico.preco_padrao))
                    desconto_item = to_decimal(item.get('desconto_item', "0.00"))

                    subtotal_item = (preco_unitario * quantidade) - desconto_item
                    iva_percentual = getattr(servico, 'iva_percentual', 14)
                    iva_item = subtotal_item * (iva_percentual / Decimal('100.00'))
                    total_item = subtotal_item + iva_item

                    subtotal_final += subtotal_item
                    desconto_final += desconto_item
                    iva_final += iva_item
                    total_final += total_item
                    
                    itens_processados.append({
                        'tipo': 'servico',
                        'servico_obj': servico,
                        'quantidade': quantidade,
                        'preco_unitario': preco_unitario,
                        'desconto_item': desconto_item,
                        'subtotal_item': subtotal_item,
                        'iva_percentual': iva_percentual,
                        'iva_valor': iva_item,
                        'total_item': total_item,
                        'duracao': servico.duracao_padrao_minutos,
                        'instrucoes': servico.instrucoes_padrao
                    })
                    print(f"Item processado (serviço). ID: {servico_id}, Quantidade: {quantidade}")

                else:
                    raise ValueError("Item sem 'produto_id' ou 'servico_id'.")

            print("\nEtapa 2: Iniciando a criação da Venda.")

            # 2. CRIAÇÃO E SALVAMENTO DA VENDA
            troco = valor_pago_decimal - total_final if valor_pago_decimal >= total_final else Decimal('0.00')

            nova_venda = Venda(
                cliente=cliente,
                forma_pagamento=forma_pagamento,
                empresa=empresa,
                loja=loja,
                vendedor=funcionario,
                subtotal=subtotal_final,
                desconto_valor=desconto_final,
                iva_valor=iva_final,
                total=total_final,
                valor_pago=valor_pago_decimal,
                troco=troco,
                status='finalizada',
                observacoes=data.get('observacoes', '')
            )
            nova_venda.save()
            print(f"Venda criada com sucesso. ID: {nova_venda.id}")

            print("\nEtapa 3: Criando Itens da Venda e atualizando estoque (produtos).")
            for item in itens_processados:
                if item['tipo'] == 'produto':
                    ItemVenda.objects.create(
                        venda=nova_venda,
                        produto=item['produto_obj'],
                        nome_produto=item['produto_obj'].nome_produto,
                        quantidade=item['quantidade'],
                        preco_unitario=item['preco_unitario'],
                        desconto_item=item['desconto_item'],
                        subtotal_sem_iva=item['subtotal_item'],
                        iva_percentual=item['iva_percentual'],
                        iva_valor=item['iva_valor'],
                        total=item['total_item']
                    )
                    # Atualiza o estoque
                    item['produto_obj'].estoque_atual = F('estoque_atual') - item['quantidade']
                    item['produto_obj'].save(update_fields=['estoque_atual'])
                elif item['tipo'] == 'servico':
                    ItemVenda.objects.create(
                        venda=nova_venda,
                        servico=item['servico_obj'],
                        nome_servico=item['servico_obj'].nome,  # novo campo
                        duracao_servico_padrao=timedelta(minutes=item['duracao']),  # conversão int -> timedelta
                        instrucoes_servico=item['instrucoes'],  # novo campo
                        quantidade=item['quantidade'],
                        preco_unitario=item['preco_unitario'],
                        subtotal_sem_iva=item['subtotal_item'],
                        iva_percentual=item['iva_percentual'],
                        iva_valor=item['iva_valor'],
                        desconto_item=item['desconto_item'],
                        total=item['total_item']
                    )


            # 4. Pagamento e Pontos
            PagamentoVenda.objects.create(
                venda=nova_venda,
                forma_pagamento=forma_pagamento,
                valor_pago=valor_pago_decimal
            )
            if cliente:
                Ponto.objects.create(
                    cliente=cliente,
                    valor=nova_venda.total,
                    data=timezone.now().date()
                )

        return JsonResponse({
            'success': True,
            'message': f'Venda {nova_venda.numero_venda} finalizada com sucesso.',
            'venda_id': nova_venda.id
        })

    except json.JSONDecodeError:
        logger.error("Erro: JSON inválido")
        return JsonResponse({'success': False, 'message': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        logger.exception(f"Erro inesperado: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erro na venda: {str(e)}'}, status=500)



@login_required
def formas_pagamento_api(request):
    """
    API para buscar todas as formas de pagamento ativas da empresa do utilizador logado.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)

    try:
        # AQUI está a solução correta
        empresa_id = request.user.empresa.id 
        
        formas = FormaPagamento.objects.filter(empresa_id=empresa_id, ativa=True).order_by('ordem_exibicao')
        
        data = [{
            'id': f.id,
            'nome': f.nome,
        } for f in formas]

        return JsonResponse({'success': True, 'formas_pagamento': data})
    except AttributeError:
        # Caso o utilizador não tenha uma empresa associada
        return JsonResponse({'success': False, 'message': 'Utilizador não tem empresa associada.'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

from django.contrib.auth.decorators import permission_required 




# Fatura recibo

 # Fatura recibo
@require_GET
@permission_required('vendas.view_venda', raise_exception=True) 
def fatura_pdf_view(request, venda_id, tipo):
    """
    Gera uma fatura em PDF para uma venda específica.
    Otimizado para consultas eficientes ao banco de dados.
    """
    
    venda = get_object_or_404(
        Venda.objects.select_related(
            'empresa__config_fiscal',
            'cliente',
            'forma_pagamento'
        ).prefetch_related(
            'itens__produto',
            'itens__servico',  # Adicionar serviços
            Prefetch('empresa__personalizacaointerface_set', queryset=PersonalizacaoInterface.objects.all()),
            Prefetch('empresa__config_fiscal__dados_bancarios', queryset=DadosBancarios.objects.all()),
            Prefetch('cliente__enderecos', queryset=EnderecoCliente.objects.filter(endereco_principal=True) or EnderecoCliente.objects.all()),
        ), 
        pk=venda_id
    )

    # 2. CONSOLIDAÇÃO DE DADOS: Prepara os dicionários de contexto
    
    # Informações da Empresa
    empresa_info = {}
    empresa = venda.empresa
    if empresa:
        config_fiscal = getattr(empresa, 'config_fiscal', None)
        personalizacao = empresa.personalizacaointerface_set.first()
        logo_url = request.build_absolute_uri(personalizacao.logo_principal.url) if personalizacao and personalizacao.logo_principal else None
        
        if config_fiscal:
            empresa_info = {
                'razao_social': config_fiscal.razao_social,
                'nome_fantasia': config_fiscal.nome_fantasia,
                'nif': config_fiscal.nif,
                'email': config_fiscal.email,
                'site': config_fiscal.site,
                'telefone': config_fiscal.telefone,
                'endereco': config_fiscal.endereco,
                'logo_url': logo_url,
            }
        else:
            empresa_info = {'logo_url': logo_url}

    # Informações Bancárias
    dados_bancarios = []
    if empresa and hasattr(empresa, 'config_fiscal') and empresa.config_fiscal:
        for conta in empresa.config_fiscal.dados_bancarios.all():
            dados_bancarios.append({
                'nome_banco': conta.nome_banco,
                'numero_conta': conta.numero_conta,
                'iban': conta.iban,
                'swift': conta.swift,
            })

    # Informações do Cliente
    cliente_info = {}
    cliente = venda.cliente
    if cliente:
        nome_cliente = cliente.razao_social or cliente.nome_fantasia if cliente.tipo_cliente == 'pessoa_juridica' else cliente.nome_completo
        nif_cliente = cliente.nif if cliente.tipo_cliente == 'pessoa_juridica' else (cliente.bi or 'N/A')
        endereco_principal = cliente.enderecos.first()
        cliente_info = {
            'nome': nome_cliente,
            'nif': nif_cliente,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': endereco_principal.endereco_completo if endereco_principal else 'N/A',
        }

    # Informações da Fatura
    fatura_info = {
        'numero': venda.numero_venda,
        'data_emissao': venda.data_venda,
        'observacoes': venda.observacoes,
        'tipo_venda': venda.get_tipo_venda_display(),
        'forma_pagamento': venda.forma_pagamento.nome if venda.forma_pagamento else 'N/A',
        'status': venda.get_status_display(),
    }
    
    # **CORREÇÃO: Usar valores já calculados e verificar produto/serviço corretamente**
    itens_venda = []
    for item in venda.itens.all():
        # Verificar se tem produto (usando hasattr para evitar RelatedObjectDoesNotExist)
        if hasattr(item, 'produto') and item.produto:
            # Calcular percentual do desconto para exibição
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'produto',
                'produto': item.produto,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,  # Valor em Kz
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
            })
        # Verificar se tem serviço
        elif hasattr(item, 'servico') and item.servico:
            # Calcular percentual do desconto para exibição
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'servico',
                'servico': item.servico,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,  # Valor em Kz
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
                'duracao': getattr(item, 'duracao_servico_padrao', None),
                'instrucoes': getattr(item, 'instrucoes_servico', None),
            })
        else:
            # Item sem produto nem serviço - usar campos diretos do ItemVenda
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'item',
                'nome': getattr(item, 'nome_produto', '') or getattr(item, 'nome_servico', 'Item'),
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
            })

    # Totais da Venda (usar valores já calculados)
    totais = {
        'subtotal': venda.subtotal,
        'desconto_valor': venda.desconto_valor,
        'iva_valor': venda.iva_valor,
        'total': venda.total,
        'valor_pago': venda.valor_pago,
        'troco': venda.troco,
    }

    # Escolha do template
    if tipo == 'a4':
        template_name = 'faturas/fatura_a4_pdf.html'
        filename = f'Fatura_A4_Venda_{venda.numero_venda}.pdf'
    elif tipo == '80mm':
        template_name = 'faturas/fatura_80mm_pdf.html'
        filename = f'Fatura_80mm_Venda_{venda.numero_venda}.pdf'
    else:
        return HttpResponse("Tipo de fatura inválido. Use 'a4' ou '80mm'.", status=400)
    

    # QR Code
    qr_code_base64 = gerar_qr_fatura(venda, request=request)  # 🔑

    context = {
        'empresa': empresa_info,
        'cliente': cliente_info,
        'fatura': fatura_info,
        'itens_venda': itens_venda,
        'totais': totais,
        'dados_bancarios': dados_bancarios,
        'qr_code_base64': qr_code_base64,  # 🔑
        'request': request,
    }
    
    html_string = render_to_string(template_name, context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@require_GET
@permission_required('vendas.view_faturacredito', raise_exception=True) 
def fatura_credito_pdf_view(request, fatura_id, tipo):
    """
    Gera uma Fatura a Crédito (FT) em PDF para uma FaturaCredito específica.
    Reutiliza a estrutura de dados da fatura recibo (A4).
    """
    
    # 1. CONSULTA DE DADOS OTIMIZADA (FT)
    fatura_credito = get_object_or_404(
        FaturaCredito.objects.select_related(
            'empresa__config_fiscal',
            'cliente'
        ).prefetch_related(
            Prefetch('itens', queryset=ItemFatura.objects.select_related('produto', 'servico')), 
            Prefetch('empresa__personalizacaointerface_set', queryset=PersonalizacaoInterface.objects.all()),
            Prefetch('empresa__config_fiscal__dados_bancarios', queryset=DadosBancarios.objects.all()),
            Prefetch('cliente__enderecos', queryset=EnderecoCliente.objects.filter(endereco_principal=True) or EnderecoCliente.objects.all()),
        ), 
        pk=fatura_id
    )

    # 2. CONSOLIDAÇÃO DE DADOS: Extração de informações da Empresa e Cliente

    empresa = fatura_credito.empresa
    cliente = fatura_credito.cliente

    # a) Informações da Empresa e Bancárias
    empresa_info = {}
    dados_bancarios = []
    
    if empresa:
        config_fiscal = getattr(empresa, 'config_fiscal', None)
        personalizacao = empresa.personalizacaointerface_set.first()
        logo_url = request.build_absolute_uri(personalizacao.logo_principal.url) if personalizacao and personalizacao.logo_principal else None
        
        if config_fiscal:
            empresa_info = {
                'razao_social': config_fiscal.razao_social,
                'nome_fantasia': config_fiscal.nome_fantasia,
                'nif': config_fiscal.nif,
                'email': config_fiscal.email,
                'site': config_fiscal.site,
                'telefone': config_fiscal.telefone,
                'endereco': config_fiscal.endereco,
                'logo_url': logo_url,
            }
        else:
            empresa_info = {'logo_url': logo_url}

        # Lógica Bancária
        if config_fiscal:
            for conta in config_fiscal.dados_bancarios.all():
                dados_bancarios.append({
                    'nome_banco': conta.nome_banco,
                    'numero_conta': conta.numero_conta,
                    'iban': conta.iban,
                    'swift': conta.swift,
                })

    # b) Informações do Cliente
    cliente_info = {}
    if cliente:
        nome_cliente = getattr(cliente, 'nome_exibicao', None) 
        if not nome_cliente:
            nome_cliente = cliente.razao_social or cliente.nome_fantasia if cliente.tipo_cliente == 'pessoa_juridica' else cliente.nome_completo
            
        nif_cliente = cliente.nif if cliente.tipo_cliente == 'pessoa_juridica' else (cliente.bi or 'N/A')
        
        endereco_principal = cliente.enderecos.first()
        cliente_info = {
            'nome': nome_cliente,
            'nif': nif_cliente,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': endereco_principal.endereco_completo if endereco_principal else 'N/A',
        }

    # c) Informações da Fatura
    fatura_info = {
        'numero': fatura_credito.numero_fatura, 
        'data_emissao': fatura_credito.data_emissao,
        'data_vencimento': fatura_credito.data_vencimento,  # Adicionado para FT
        'observacoes': fatura_credito.observacoes,
        'tipo_venda': "Fatura a Crédito (FT)", 
        'forma_pagamento': 'Crédito', 
        'status': fatura_credito.get_status_display(),
    }
    
    # d) Itens da Fatura
    itens_fatura = []
    desconto_total_itens = Decimal('0.00')

    for item in fatura_credito.itens.all():
        subtotal_item = item.preco_unitario * item.quantidade
        desconto_percentual = (item.desconto_item / subtotal_item * Decimal('100.00')) if subtotal_item > Decimal('0.00') else Decimal('0.00')
        desconto_total_itens += item.desconto_item

        itens_fatura.append({
            'tipo': 'produto' if item.produto_id else 'servico',
            'produto': item.produto,
            'servico': item.servico,
            'nome': item.nome_item, 
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario,
            'desconto_valor': item.desconto_item,
            'desconto_percentual': desconto_percentual,
            'iva_percentual': item.iva_percentual,
            'iva_valor': item.iva_valor,
            'total': item.total,
        })

    # e) Totais da Fatura
    totais = {
        'subtotal': fatura_credito.subtotal,
        'desconto_valor': desconto_total_itens,
        'iva_valor': fatura_credito.iva_valor,
        'total': fatura_credito.total_faturado, 
        'valor_pago': Decimal('0.00'), 
        'troco': Decimal('0.00'),
    }

    # 3. ESCOLHA DO TEMPLATE E CONTEXTO
    template_name = 'faturas/fatura_a4_pdf.html' 
    filename = f'Fatura_Credito_FT_{fatura_credito.numero_fatura}.pdf'


    qr_code_base64 = gerar_qr_fatura(fatura_credito, request) # 🔑
    # qr_code_base64 = gerar_qr_fatura(fatura, request=request)  # 🔑

    context = {
        'empresa': empresa_info,
        'cliente': cliente_info,
        'fatura': fatura_info,
        'itens_venda': itens_fatura, 
        'totais': totais,
        'dados_bancarios': dados_bancarios,
        'qr_code_base64': qr_code_base64,  # 🔑
        'request': request,
    }
    
    # 4. GERAÇÃO DO PDF
    html_string = render_to_string(template_name, context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@require_GET
@permission_required('vendas.view_faturaproforma', raise_exception=True) 
def proforma_pdf_view(request, proforma_id):
    """
    Gera uma Proforma em PDF seguindo o padrão da fatura_pdf_view.
    Otimizado para consultas eficientes ao banco de dados.
    """
    
    proforma = get_object_or_404(
        FaturaProforma.objects.select_related(
            'empresa__config_fiscal',
            'cliente'
        ).prefetch_related(
            'itens__produto',
            'itens__servico',  # Adicionar serviços
            Prefetch('empresa__personalizacaointerface_set', queryset=PersonalizacaoInterface.objects.all()),
            Prefetch('empresa__config_fiscal__dados_bancarios', queryset=DadosBancarios.objects.all()),
            Prefetch('cliente__enderecos', queryset=EnderecoCliente.objects.filter(endereco_principal=True) or EnderecoCliente.objects.all()),
        ), 
        pk=proforma_id
    )

    # 2. CONSOLIDAÇÃO DE DADOS: Prepara os dicionários de contexto
    
    # Informações da Empresa
    empresa_info = {}
    empresa = proforma.empresa
    if empresa:
        config_fiscal = getattr(empresa, 'config_fiscal', None)
        personalizacao = empresa.personalizacaointerface_set.first()
        logo_url = request.build_absolute_uri(personalizacao.logo_principal.url) if personalizacao and personalizacao.logo_principal else None
        
        if config_fiscal:
            empresa_info = {
                'razao_social': config_fiscal.razao_social,
                'nome_fantasia': config_fiscal.nome_fantasia,
                'nif': config_fiscal.nif,
                'email': config_fiscal.email,
                'site': config_fiscal.site,
                'telefone': config_fiscal.telefone,
                'endereco': config_fiscal.endereco,
                'logo_url': logo_url,
            }
        else:
            empresa_info = {'logo_url': logo_url}

    # Informações Bancárias
    dados_bancarios = []
    if empresa and hasattr(empresa, 'config_fiscal') and empresa.config_fiscal:
        for conta in empresa.config_fiscal.dados_bancarios.all():
            dados_bancarios.append({
                'nome_banco': conta.nome_banco,
                'numero_conta': conta.numero_conta,
                'iban': conta.iban,
                'swift': conta.swift,
            })

    # Informações do Cliente
    cliente_info = {}
    cliente = proforma.cliente
    if cliente:
        nome_cliente = cliente.razao_social or cliente.nome_fantasia if cliente.tipo_cliente == 'pessoa_juridica' else cliente.nome_completo
        nif_cliente = cliente.nif if cliente.tipo_cliente == 'pessoa_juridica' else (cliente.bi or 'N/A')
        endereco_principal = cliente.enderecos.first()
        cliente_info = {
            'nome': nome_cliente,
            'nif': nif_cliente,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': endereco_principal.endereco_completo if endereco_principal else 'N/A',
        }

    # Informações da Proforma
    fatura_info = {
        'numero': proforma.numero_proforma,
        'data_emissao': proforma.data_emissao,
        'data_vencimento': proforma.data_validade,  # Data de validade da proforma
        'observacoes': proforma.observacoes,
        'tipo_venda': "Fatura Proforma",
        'forma_pagamento': 'Orçamento',
        'status': proforma.get_status_display(),
    }
    
    # **TRATAMENTO DETALHADO DOS ITENS: Seguindo o padrão da fatura_pdf_view**
    itens_venda = []
    for item in proforma.itens.all():
        # Verificar se tem produto (usando hasattr para evitar RelatedObjectDoesNotExist)
        if hasattr(item, 'produto') and item.produto:
            # Calcular percentual do desconto para exibição
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'produto',
                'produto': item.produto,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,  # Valor em Kz
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
            })
        # Verificar se tem serviço
        elif hasattr(item, 'servico') and item.servico:
            # Calcular percentual do desconto para exibição
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'servico',
                'servico': item.servico,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,  # Valor em Kz
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
                'duracao': getattr(item, 'duracao_servico_padrao', None),
                'instrucoes': getattr(item, 'instrucoes_servico', None),
            })
        else:
            # Item sem produto nem serviço - usar campos diretos do ItemProforma
            subtotal_item = item.preco_unitario * item.quantidade
            desconto_percentual = (item.desconto_item / subtotal_item * 100) if subtotal_item > 0 else 0
            
            itens_venda.append({
                'tipo': 'item',
                'nome': getattr(item, 'nome_produto', '') or getattr(item, 'nome_servico', '') or getattr(item, 'nome_item', 'Item'),
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'desconto_valor': item.desconto_item,
                'desconto_percentual': desconto_percentual,
                'iva_percentual': item.iva_percentual,
                'iva_valor': item.iva_valor,
                'total': item.total,
            })

    # Totais da Proforma (usar valores já calculados)
    totais = {
        'subtotal': proforma.subtotal,
        'desconto_valor': proforma.desconto_global,  # Proforma tem desconto_global
        'iva_valor': proforma.iva_valor,
        'total': proforma.total,
        # Para Proforma: Estes campos devem ser 0 (não há pagamento ainda)
        'valor_pago': Decimal('0.00'),
        'troco': Decimal('0.00'),
    }

    # Template sempre A4 para proforma
    template_name = 'faturas/fatura_a4_pdf.html'
    filename = f'Proforma_{proforma.numero_proforma}.pdf'

    qr_code_base64 = gerar_qr_fatura(proforma, request=request)  # 🔑
    logger.debug("QR (prefix 200): %s", (qr_code_base64 or "")[:200])
    context = {
        'empresa': empresa_info,
        'cliente': cliente_info,
        'fatura': fatura_info,
        'itens_venda': itens_venda,
        'totais': totais,
        'dados_bancarios': dados_bancarios,
        'qr_code_base64': qr_code_base64,  # 🔑
        'request': request,
    }
    
    html_string = render_to_string(template_name, context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def recibo_pdf_view(request, recibo_id):
    """
    Gera o PDF de um Recibo de Tesouraria (Liquidação de Fatura a Crédito).
    """
    try:
        # 1. Obter o Recibo e a Fatura de Origem
        recibo = get_object_or_404(Recibo, pk=recibo_id)
        fatura_original = recibo.fatura  # fatura liquidada
        
        # 2. Obter Dados da Empresa e Bancários
        empresa = Empresa.objects.first() 
        dados_bancarios = ContaBancaria.objects.filter(empresa=empresa, ativa=True)

        # 3. Preparar o Contexto dos Dados
        documento_recibo = {
            'numero': recibo.numero_recibo,  # Ex: REC/2025/0001
            'tipo_venda': 'Recibo',
            'data_emissao': recibo.data_recibo,
            'status': 'Liquidado',
            'observacoes': f"Refere-se à Fatura: {fatura_original.numero_fatura}, "
                           f"Valor Liquidado: {recibo.valor_recebido:.2f} Kz.",
            'forma_pagamento': recibo.forma_pagamento,
            'data_vencimento': None  # Não aplicável a Recibos
        }

        # Itens simulados (recibo não tem itens)
        itens_recibo = [{
            'nome': f"Pagamento da Fatura {fatura_original.numero_fatura} "
                    f"de {fatura_original.total_faturado:.2f} Kz",
            'quantidade': 1,
            'preco_unitario': recibo.valor_recebido,
            'desconto_percentual': 0.0,
            'iva_percentual': 0.0,
            'total': recibo.valor_recebido,
            'tipo': 'servico'
        }]

        # Totais
        totais_recibo = {
            'subtotal': recibo.valor_recebido,
            'iva_valor': 0.00,
            'total': recibo.valor_recebido,
            'desconto_valor': 0.00,
            'valor_pago': recibo.valor_recebido,
            'troco': 0.00
        }

        # 4. Cliente vem da fatura original
        cliente_info = {}
        if fatura_original.cliente:
            cliente = fatura_original.cliente
            nome_cliente = getattr(cliente, 'nome_exibicao', None)
            if not nome_cliente:
                nome_cliente = (cliente.razao_social or cliente.nome_fantasia 
                                if cliente.tipo_cliente == 'pessoa_juridica' 
                                else cliente.nome_completo)

            nif_cliente = cliente.nif if cliente.tipo_cliente == 'pessoa_juridica' else (cliente.bi or 'N/A')
            endereco_principal = cliente.enderecos.first()

            cliente_info = {
                'nome': nome_cliente,
                'nif': nif_cliente,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'endereco': endereco_principal.endereco_completo if endereco_principal else 'N/A',
            }

        # 5. Gerar QR Code
        qr_code_base64 = gerar_qr_fatura(recibo, request=request)

        # 6. Contexto final
        context = {
            'fatura': documento_recibo,
            'itens_venda': itens_recibo,
            'totais': totais_recibo,
            'cliente': cliente_info,  # ✅ agora passa o dict
            'empresa': empresa,
            'dados_bancarios': dados_bancarios,
            'qr_code_base64': qr_code_base64,
            'request': request,
        }

        # 7. Renderizar PDF
        html_string = render_to_string('faturas/recibo_a4_pdf.html', context)
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{recibo.numero_recibo}.pdf"'
        return response

    except FaturaCredito.DoesNotExist:
        return HttpResponse("Erro: Fatura liquidada não encontrada.", status=404)
    except Recibo.DoesNotExist:
        return HttpResponse("Erro: Recibo não encontrado.", status=404)
    except Exception as e:
        print(f"Erro ao gerar PDF do Recibo: {e}")
        return HttpResponse(f"Erro interno do servidor ao gerar PDF: {e}", status=500)



from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from weasyprint import HTML # Assumindo que você usa WeasyPrint


from .models import FaturaCredito, ItemFatura 
#-------------------------------------------





from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML # Assumindo WeasyPrint
#original

@require_http_methods(["POST"])
@login_required
def atualizar_observacoes_venda(request, venda_id):
    """Atualiza as observações de uma venda"""
    try:
        data = json.loads(request.body)
        observacoes = data.get('observacoes', '')
        
        venda = get_object_or_404(Venda, id=venda_id, empresa=request.user.funcionario.empresa)
        venda.observacoes = observacoes
        venda.save(update_fields=['observacoes'])
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)






@login_required
def documentos_dashboard_view(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('acessar_documentos', False):
        return JsonResponse({'success': False, 'message': 'Sem permissao para finalizar para acessar documentos.'}, status=403)

    """Dashboard geral de documentos fiscais"""
    
    # Período dos últimos 30 dias
    data_inicio = timezone.now().date() - timedelta(days=30)
    
    # Estatísticas de Vendas (FR)
    vendas_stats = Venda.objects.filter(
        empresa=request.user.empresa,
        data_venda__gte=data_inicio
    ).aggregate(
        total_vendas=Count('id'),
        total_faturamento=Sum('total'),
        total_vendas_finalizadas=Count('id', filter=models.Q(status='finalizada'))
    )
    
    # Estatísticas de Faturas a Crédito (FT)
    try:
        faturas_credito_stats = FaturaCredito.objects.filter(
            empresa=request.user.empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_faturas=Count('id'),
            total_valor=Sum('total_faturado'),
            pendentes=Count('id', filter=models.Q(status='pendente')),
            liquidadas=Count('id', filter=models.Q(status='liquidada'))
        )
    except:
        faturas_credito_stats = {
            'total_faturas': 0,
            'total_valor': 0,
            'pendentes': 0,
            'liquidadas': 0
        }
    
    # Estatísticas de Recibos (REC)
    try:
        recibos_stats = Recibo.objects.filter(
            empresa=request.user.empresa,
            data_recibo__gte=data_inicio
        ).aggregate(
            total_recibos=Count('id'),
            total_recebido=Sum('valor_recebido')
        )
    except:
        recibos_stats = {
            'total_recibos': 0,
            'total_recebido': 0
        }
    
    # Estatísticas de Proformas
    try:
        proformas_stats = FaturaProforma.objects.filter(
            empresa=request.user.empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_proformas=Count('id'),
            total_valor=Sum('total'),
            aceitas=Count('id', filter=models.Q(status='aceite')),
            pendentes=Count('id', filter=models.Q(status='emitida'))
        )
    except:
        proformas_stats = {
            'total_proformas': 0,
            'total_valor': 0,
            'aceitas': 0,
            'pendentes': 0
        }
    
    # Vendas recentes
    vendas_recentes = Venda.objects.filter(
        empresa=request.user.empresa
    ).select_related('cliente').order_by('-data_venda')[:10]
    
    context = {
        'title': 'Dashboard de Documentos',
        'data_inicio': data_inicio,
        'vendas_stats': vendas_stats,
        'faturas_credito_stats': faturas_credito_stats,
        'recibos_stats': recibos_stats,
        'proformas_stats': proformas_stats,
        'vendas_recentes': vendas_recentes,
    }
    
    return render(request, 'vendas/documentos_dashboard.html', context)


# apps/vendas/views.py - ADICIONAR essas views

@login_required
def nova_fatura_credito(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_faturacredito', False):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para emitir crédito a crédito.'}, status=403)
    
    context = {
        'title': 'Nova Fatura a Crédito (FT)',
        'tipo_documento': 'FT'
    }
    return render(request, 'vendas/nova_fatura_credito.html', context)


@login_required
def nova_proforma(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_proforma'):
        return JsonResponse({'success': False, 'message': 'Você não tem permissão para emitir proformas a crédito.'}, status=403)
    
    
    """Interface para criar nova Proforma (Orçamento)"""
    context = {
        'title': 'Nova Proforma (Orçamento)',
        'tipo_documento': 'PF'
    }
    return render(request, 'vendas/nova_proforma.html', context)

@login_required
def contas_receber(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('acessar_financeiro'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para emitir crédito a crédito.'}, status=403)
    
    """Relatório de Contas a Receber (Faturas a Crédito pendentes)"""
    try:
        faturas_pendentes = (
            FaturaCredito.objects.filter(
                empresa=request.user.empresa,
                status__in=['pendente', 'parcial']
            )
            .select_related('cliente')
            .order_by('data_vencimento')
        )
        
        # Adiciona saldo em cada fatura
        for f in faturas_pendentes:
            f.saldo = (f.total_faturado or 0) - (f.valor_pago or 0)
        
        # Calcular totais
        total_pendente = faturas_pendentes.aggregate(
            total=Sum('total_faturado'),
            total_pago=Sum('valor_pago')
        )
        
        total_a_receber = (total_pendente['total'] or 0) - (total_pendente['total_pago'] or 0)
    
    except Exception:
        faturas_pendentes = []
        total_a_receber = 0
    
    context = {
        'title': 'Contas a Receber',
        'faturas_pendentes': faturas_pendentes,
        'total_a_receber': total_a_receber,
    }
    return render(request, 'vendas/contas_receber.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def finalizar_fatura_credito_api(request):

    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_faturacredito', False):
        return JsonResponse({'success': False, 'message': 'Sem permissão para finalizar fatura a crédito.'}, status=403)
    
    try:

        funcionario = request.user.funcionario
        if not funcionario.pode_realizar_acao('vender'):
            # Permissão de cargo negada!
            return JsonResponse({'success': False, 'message': 'O seu cargo não permite finalizar nota de crédito.'}, status=403)
        
        data = json.loads(request.body)
        
        
        # Validações básicas
        if not data.get('cliente_id'):
            return JsonResponse({'success': False, 'message': 'Cliente é obrigatório para faturas a crédito'})
        
        if not data.get('data_vencimento'):
            return JsonResponse({'success': False, 'message': 'Data de vencimento é obrigatória'})
        
        with transaction.atomic():
            # Criar a Fatura a Crédito
            fatura_credito = FaturaCredito.objects.create(
                empresa=request.user.empresa,
                cliente_id=data['cliente_id'],
                data_vencimento=data['data_vencimento'],
                subtotal=Decimal(str(data.get('subtotal', 0))),
                iva_valor=Decimal(str(data.get('iva_valor', 0))),
                total_faturado=Decimal(str(data.get('total', 0))),
                observacoes=data.get('observacoes', '')
            )
            
            # Criar os itens da fatura
            for item_data in data.get('itens', []):
                ItemFatura.objects.create(
                    fatura=fatura_credito,
                    produto_id=item_data.get('produto_id'),
                    servico_id=item_data.get('servico_id'),
                    nome_item=item_data.get('nome_item', ''),
                    quantidade=Decimal(str(item_data.get('quantidade', 1))),
                    preco_unitario=Decimal(str(item_data.get('preco_unitario', 0))),
                    desconto_item=Decimal(str(item_data.get('desconto_item', 0))),
                    iva_percentual=Decimal(str(item_data.get('iva_percentual', 0))),
                    iva_valor=Decimal(str(item_data.get('iva_valor', 0))),
                    total=Decimal(str(item_data.get('total', 0)))
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Fatura a crédito criada com sucesso!',
            'fatura_id': fatura_credito.id,
            'numero_fatura': fatura_credito.numero_fatura
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar fatura a crédito: {str(e)}'
        })

#-------------------------------------------------------

@login_required
def faturas_recibo_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('ver_vender'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para ver lista de vendas.'}, status=403)
    
    """Lista das Faturas Recibo (vendas do PDV)"""
    vendas = Venda.objects.filter(
        empresa=request.user.empresa
    ).select_related('cliente', 'forma_pagamento').order_by('-data_venda')
    
    context = {
        'vendas': vendas,
        'title': 'Faturas Recibo (FR)'
    }
    return render(request, 'vendas/faturas_recibo_lista.html', context)

@login_required
def faturas_credito_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_faturacredito', False):
        return JsonResponse({'success': False, 'message': 'Sem permissão para acessar faturas a crédito.'}, status=403)
    
    try:
        faturas = FaturaCredito.objects.filter(
            empresa=request.user.empresa
        ).select_related('cliente').order_by('-data_emissao')
    except:
        faturas = []
    
    context = {
        'faturas': faturas,
        'title': 'Faturas a Crédito (FT)'
    }
    return render(request, 'vendas/faturas_credito_lista.html', context)

@login_required
def recibos_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_recibo', False):
        return JsonResponse({'success': False, 'message': 'Sem permissão para acessar recibos.'}, status=403)
    
    try:
        recibos = Recibo.objects.filter(
            empresa=request.user.empresa
        ).select_related('fatura__cliente').order_by('-data_recibo')
    except:
        recibos = []
    
    context = {
        'recibos': recibos,
        'title': 'Recibos (REC)'
    }
    return render(request, 'vendas/recibos_lista.html', context)

@login_required
def proformas_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_faturacredito', False):
        return JsonResponse({'success': False, 'message': 'Sem permissão para acessar fatura proformas.'}, status=403)
    
    try:
        proformas = FaturaProforma.objects.filter(
            empresa=request.user.empresa
        ).select_related('cliente').order_by('-data_emissao')
    except:
        proformas = []
    
    context = {
        'proformas': proformas,
        'title': 'Proformas'
    }
    return render(request, 'vendas/proformas_lista.html', context)
#------------------------------------------------------

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.db import models

@login_required
def vendas_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('ver_vendas'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para ver lista de vendas.'}, status=403)
    
    """Lista das vendas realizadas (Faturas Recibo)"""
    vendas = Venda.objects.filter(
        empresa=request.user.empresa
    ).select_related('cliente', 'forma_pagamento').order_by('-data_venda')[:50]
    
    context = {
        'vendas': vendas,
        'title': 'Vendas Realizadas'
    }
    return render(request, 'vendas/vendas_lista.html', context)

@login_required
def documentos_dashboard_view(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('acessar_documentos'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para acessar documentos.'}, status=403)
    
    """Dashboard geral de documentos fiscais"""
    
    # Período dos últimos 30 dias
    data_inicio = timezone.now().date() - timedelta(days=30)
    
    # Estatísticas de Vendas (FR)
    vendas_stats = Venda.objects.filter(
        empresa=request.user.empresa,
        data_venda__gte=data_inicio
    ).aggregate(
        total_vendas=Count('id'),
        total_faturamento=Sum('total'),
        total_vendas_finalizadas=Count('id', filter=models.Q(status='finalizada'))
    )
    
    # Estatísticas de Faturas a Crédito (FT) - com tratamento de erro
    try:
        faturas_credito_stats = FaturaCredito.objects.filter(
            empresa=request.user.empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_faturas=Count('id'),
            total_valor=Sum('total_faturado'),
            pendentes=Count('id', filter=models.Q(status='pendente')),
            liquidadas=Count('id', filter=models.Q(status='liquidada'))
        )
    except:
        faturas_credito_stats = {
            'total_faturas': 0,
            'total_valor': 0,
            'pendentes': 0,
            'liquidadas': 0
        }
    
    # Estatísticas de Recibos (REC) - com tratamento de erro
    try:
        recibos_stats = Recibo.objects.filter(
            empresa=request.user.empresa,
            data_recibo__gte=data_inicio
        ).aggregate(
            total_recibos=Count('id'),
            total_recebido=Sum('valor_recebido')
        )
    except:
        recibos_stats = {
            'total_recibos': 0,
            'total_recebido': 0
        }
    
    # Estatísticas de Proformas - com tratamento de erro
    try:
        proformas_stats = FaturaProforma.objects.filter(
            empresa=request.user.empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_proformas=Count('id'),
            total_valor=Sum('total'),
            aceitas=Count('id', filter=models.Q(status='aceite')),
            pendentes=Count('id', filter=models.Q(status='emitida'))
        )
    except:
        proformas_stats = {
            'total_proformas': 0,
            'total_valor': 0,
            'aceitas': 0,
            'pendentes': 0
        }
    
    # Vendas recentes
    vendas_recentes = Venda.objects.filter(
        empresa=request.user.empresa
    ).select_related('cliente').order_by('-data_venda')[:10]
    
    context = {
        'title': 'Dashboard de Documentos',
        'data_inicio': data_inicio,
        'vendas_stats': vendas_stats,
        'faturas_credito_stats': faturas_credito_stats,
        'recibos_stats': recibos_stats,
        'proformas_stats': proformas_stats,
        'vendas_recentes': vendas_recentes,
    }
    
    return render(request, 'vendas/documentos_dashboard.html', context)

@login_required
def faturas_recibo_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('ver_vendas'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para ver lista de faturas FR.'}, status=403)
    
    """Lista das Faturas Recibo (vendas do PDV)"""
    vendas = Venda.objects.filter(
        empresa=request.user.empresa
    ).select_related('cliente', 'forma_pagamento').order_by('-data_venda')
    
    context = {
        'vendas': vendas,
        'title': 'Faturas Recibo (FR)'
    }
    return render(request, 'vendas/faturas_recibo_lista.html', context)

@login_required
def faturas_credito_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.permissoes_cargo.get('emitir_faturacredito', False):
        return JsonResponse({'success': False, 'message': 'Sem permissão para acessar faturas a crédito.'}, status=403)
    
    try:
        faturas = FaturaCredito.objects.filter(
            empresa=request.user.empresa
        ).select_related('cliente').order_by('-data_emissao')
    except:
        faturas = []
    
    context = {
        'faturas': faturas,
        'title': 'Faturas a Crédito (FT)'
    }
    return render(request, 'vendas/faturas_credito_lista.html', context)

@login_required
def recibos_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_recibo'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para ver lista de recibos.'}, status=403)
    
    """Lista dos Recibos"""
    try:
        recibos = Recibo.objects.filter(
            empresa=request.user.empresa
        ).select_related('fatura__cliente').order_by('-data_recibo')
    except:
        recibos = []
    
    context = {
        'recibos': recibos,
        'title': 'Recibos (REC)'
    }
    return render(request, 'vendas/recibos_lista.html', context)

@login_required
def proformas_lista(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_proforma'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para ver lista proformas.'}, status=403)
    
    """Lista das Proformas"""
    try:
        proformas = FaturaProforma.objects.filter(
            empresa=request.user.empresa
        ).select_related('cliente').order_by('-data_emissao')
    except:
        proformas = []
    
    context = {
        'proformas': proformas,
        'title': 'Proformas'
    }
    return render(request, 'vendas/proformas_lista.html', context)



    """API para finalizar uma Proforma"""
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        if not data.get('cliente_id'):
            return JsonResponse({'success': False, 'message': 'Cliente é obrigatório para proformas'})
        
        if not data.get('data_validade'):
            return JsonResponse({'success': False, 'message': 'Data de validade é obrigatória'})
        
        with transaction.atomic():
            # Criar a Proforma
            proforma = FaturaProforma.objects.create(
                empresa=request.user.empresa,
                cliente_id=data['cliente_id'],
                data_validade=data['data_validade'],
                subtotal=Decimal(str(data.get('subtotal', 0))),
                desconto_global=Decimal(str(data.get('desconto_global', 0))),
                iva_valor=Decimal(str(data.get('iva_valor', 0))),
                total=Decimal(str(data.get('total', 0))),
                observacoes=data.get('observacoes', '')
            )
            
            # Criar os itens da proforma
            for item_data in data.get('itens', []):
                ItemProforma.objects.create(
                    proforma=proforma,
                    produto_id=item_data.get('produto_id'),
                    servico_id=item_data.get('servico_id'),
                    quantidade=Decimal(str(item_data.get('quantidade', 1))),
                    preco_unitario=Decimal(str(item_data.get('preco_unitario', 0))),
                    desconto_item=Decimal(str(item_data.get('desconto_item', 0))),
                    iva_percentual=Decimal(str(item_data.get('iva_percentual', 0))),
                    iva_valor=Decimal(str(item_data.get('iva_valor', 0))),
                    total=Decimal(str(item_data.get('total', 0)))
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Proforma criada com sucesso!',
            'proforma_id': proforma.id,
            'numero_proforma': proforma.numero_proforma
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar proforma: {str(e)}'
        })

from decimal import Decimal
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import FaturaProforma, ItemProforma
from apps.core.services import gerar_numero_documento  # Ajusta o import conforme seu projeto

@csrf_exempt
@require_http_methods(["POST"])
def finalizar_proforma_api(request):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_proforma'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para finalizar pproformas.'}, status=403)
    
    """API para finalizar uma Proforma com geração automática de número único"""
    try:
        data = json.loads(request.body)

        # Validações básicas
        if not data.get('cliente_id'):
            return JsonResponse({'success': False, 'message': 'Cliente é obrigatório para proformas'})

        if not data.get('data_validade'):
            return JsonResponse({'success': False, 'message': 'Data de validade é obrigatória'})

        # Garante atomicidade para evitar duplicidade de número
        with transaction.atomic():
            empresa = request.user.empresa
            if not empresa:
                return JsonResponse({'success': False, 'message': 'Usuário não está associado a uma empresa'})

            # Cria a proforma sem número ainda
            proforma = FaturaProforma(
                empresa=empresa,
                cliente_id=data['cliente_id'],
                data_validade=data['data_validade'],
                subtotal=Decimal(str(data.get('subtotal', 0))),
                desconto_global=Decimal(str(data.get('desconto_global', 0))),
                iva_valor=Decimal(str(data.get('iva_valor', 0))),
                total=Decimal(str(data.get('total', 0))),
                observacoes=data.get('observacoes', '')
            )

            # Geração automática do número de forma segura
            if not proforma.numero_proforma:
                proforma.numero_proforma = gerar_numero_documento(
                    empresa=empresa,
                    tipo_documento='FP'
                )

            proforma.save()

            # Criar os itens da proforma
            for item_data in data.get('itens', []):
                ItemProforma.objects.create(
                    proforma=proforma,
                    produto_id=item_data.get('produto_id'),
                    servico_id=item_data.get('servico_id'),
                    quantidade=Decimal(str(item_data.get('quantidade', 1))),
                    preco_unitario=Decimal(str(item_data.get('preco_unitario', 0))),
                    desconto_item=Decimal(str(item_data.get('desconto_item', 0))),
                    iva_percentual=Decimal(str(item_data.get('iva_percentual', 0))),
                    iva_valor=Decimal(str(item_data.get('iva_valor', 0))),
                    total=Decimal(str(item_data.get('total', 0)))
                )

        return JsonResponse({
            'success': True,
            'message': 'Proforma criada com sucesso!',
            'proforma_id': proforma.id,
            'numero_proforma': proforma.numero_proforma
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar proforma: {str(e)}'
        })





logger = logging.getLogger(__name__)

@require_POST
@permission_required('vendas.liquidar_faturacredito', raise_exception=True) 
def liquidar_fatura_api(request, fatura_id):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('liquidar_faturacredito'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para liquidar FT.'}, status=403)
    
    """
    Endpoint API para liquidar uma Fatura a Crédito, registando o recebimento como Movimentação Financeira (Transferência).
    """
    print(f"\n[INÍCIO] Tentativa de liquidação da Fatura ID: {fatura_id}")
    
    try:
        fatura = get_object_or_404(FaturaCredito, pk=fatura_id)
        valor_a_liquidar = fatura.valor_pendente()
        
        print(f"[VERIFICAÇÃO] Valor Pendente: {valor_a_liquidar}")

        # --- 1. Verificações de Estado ---
        if fatura.status == 'liquidada':
            print("[ERRO] Fatura já liquidada.")
            return JsonResponse({'success': False, 'message': 'Esta fatura já se encontra liquidada.'}, status=400)
            
        if valor_a_liquidar <= Decimal('0.00'):
            print("[ERRO] Saldo devedor zero/negativo.")
            return JsonResponse({'success': False, 'message': 'O saldo devedor é zero ou negativo.'}, status=400)

        with transaction.atomic():
            
            # --- 2. Busca da Forma de Pagamento 'Transferência' ---
            try:
                forma_pagamento_liquidez = FormaPagamento.objects.get(
                    empresa=fatura.empresa, 
                    tipo='transferencia',
                    ativa=True
                )
                print(f"[SUCESSO] Forma Pagamento encontrada: {forma_pagamento_liquidez.nome}")
            except FormaPagamento.DoesNotExist:
                print("[ERRO] Forma de Pagamento 'Transferência' não configurada.")
                return JsonResponse({
                    'success': False, 
                    'message': 'Configuração Crítica: A forma de pagamento "Transferência" ativa não está configurada para esta empresa.'
                }, status=400) 

            # --- 3. Verificação de Destino Financeiro ---
            conta_bancaria_destino = forma_pagamento_liquidez.conta_destino
            
            if not conta_bancaria_destino:
                print("[ERRO] Forma de Pagamento sem conta bancária de destino.")
                return JsonResponse({
                    'success': False, 
                    'message': 'Configuração Crítica: A Forma de Pagamento "Transferência" não está ligada a uma Conta Bancária de Crédito válida.'
                }, status=400) 
            
            print(f"[SUCESSO] Conta Destino: {conta_bancaria_destino}")
            
            # --- 4. Busca do Plano de Contas ---
            plano_contas_receita = PlanoContas.objects.filter(
                empresa=fatura.empresa, 
                tipo_conta='receita', 
                codigo='4.1.1' 
            ).first()

            if not plano_contas_receita:
                print("[ERRO] Plano de Contas de Receita (4.1.1) não encontrado.")
                return JsonResponse({
                    'success': False, 
                    'message': 'Configuração Crítica: O Plano de Contas de Receita (código 4.1.1) não está configurado para a empresa.'
                }, status=400)
            
            print(f"[SUCESSO] Plano de Contas: {plano_contas_receita.nome}")
            
            # --- 5. Criação do Recibo (Recibo de Pagamento - REC) ---
            recibo = Recibo.objects.create(
                empresa=fatura.empresa,
                fatura=fatura, 
                valor_recebido=valor_a_liquidar,
                data_recibo=timezone.now(),
                forma_pagamento=forma_pagamento_liquidez,
            )
            print(f"[TRANSAÇÃO] Recibo criado: {recibo.numero_recibo}")
            
            # --- 6. Criação da Movimentação Financeira ---
            MovimentacaoFinanceira.objects.create(
                empresa=fatura.empresa,
                tipo_movimentacao='entrada',
                tipo_documento='transferencia',
                data_movimentacao=timezone.now().date(),
                valor=valor_a_liquidar,
                total=valor_a_liquidar,
                descricao=f'Liquidação Fatura FT {fatura.numero_fatura} (Recibo {recibo.numero_recibo})',
                
                # CAMPOS OBRIGATÓRIOS
                conta_bancaria=conta_bancaria_destino, 
                plano_contas=plano_contas_receita,
                usuario_responsavel=request.user, 
                confirmada=True, 
                data_confirmacao=timezone.now(),
                
                # CHAVES DE AUDITORIA
                recibo=recibo, 
                cliente=fatura.cliente, 
            )
            print("[TRANSAÇÃO] Movimentação Financeira criada com sucesso.")

        # --- Resposta de Sucesso ---
        print(f"[SUCESSO] Transação Atómica CONCLUÍDA. Fatura {fatura.numero_fatura} liquidada.")
        return JsonResponse({
            'success': True,
            'message': f'Fatura liquidada com sucesso. Recibo {recibo.numero_recibo} emitido.',
            'numero_fatura': fatura.numero_fatura,
            'numero_recibo': recibo.numero_recibo,
        })

    except FaturaCredito.DoesNotExist:
        print(f"[FALHA] Fatura ID {fatura_id} não encontrada.")
        return JsonResponse({'success': False, 'message': 'Fatura não encontrada.'}, status=404)
    
    except Exception as e:
        # Erro Crítico (500)
        logger.error(f"ERRO CRÍTICO NA LIQUIDAÇÃO (fatura_id={fatura_id}): {e}", exc_info=True)
        print("\n" + "="*50)
        print(f"!!! ERRO CRÍTICO (500) NO PROCESSO DE LIQUIDAÇÃO - Fatura ID: {fatura_id} !!!")
        print("MENSAGEM DE ERRO:", e)
        print("--- TRACEBACK COMPLETO (Para Debug) ---")
        traceback.print_exc() 
        print("="*50 + "\n")
        
        return JsonResponse({'success': False, 'message': 'Erro interno do servidor ao processar a liquidação. Consulte o terminal para detalhes.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def converter_proforma_api(request, proforma_id):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_faturacredito'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para emitir  fatura Crédito.'}, status=403)
    
    """API para converter uma Proforma em Fatura Recibo ou Fatura Crédito"""
    try:
        data = json.loads(request.body)
        tipo_conversao = data.get('tipo_conversao')
        
        # Verificar se o tipo de conversão é válido
        if tipo_conversao not in ['fatura_recibo', 'fatura_credito']:
            return JsonResponse({'success': False, 'message': 'Tipo de conversão inválido'})
        
        # Obter a proforma
        proforma = get_object_or_404(FaturaProforma, id=proforma_id, empresa=request.user.empresa)
        
        # Verificar se a proforma pode ser convertida
        if proforma.status != 'emitida':
            return JsonResponse({'success': False, 'message': 'Apenas proformas pendentes podem ser convertidas'})
        
        # Verificar se não está expirada
        if proforma.data_validade < timezone.now().date():
            return JsonResponse({'success': False, 'message': 'Proforma expirada não pode ser convertida'})
        
        with transaction.atomic():
            if tipo_conversao == 'fatura_recibo':
                # Converter para Fatura Recibo (Venda à Vista)
                documento_criado = _converter_para_fatura_recibo(proforma, request.user)
                tipo_nome = "Fatura Recibo (FR)"
                numero_documento = documento_criado.numero_venda
                
            else:  # fatura_credito
                # Converter para Fatura a Crédito
                documento_criado = _converter_para_fatura_credito(proforma, request.user)
                tipo_nome = "Fatura a Crédito (FT)"
                numero_documento = documento_criado.numero_fatura
            
            # Marcar proforma como convertida
            proforma.status = 'convertida'
            proforma.venda_convertida = documento_criado if tipo_conversao == 'fatura_recibo' else None
            proforma.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Proforma convertida com sucesso em {tipo_nome}: {numero_documento}',
            'documento_id': documento_criado.id,
            'numero_documento': numero_documento,
            'tipo': tipo_conversao
        })
        
    except Exception as e:
        logger.error(f"Erro ao converter proforma {proforma_id}: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erro ao converter: {str(e)}'})

def _converter_para_fatura_recibo(proforma, user):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('vender'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para converter para FR.'}, status=403)
    
    """Converte uma proforma em uma Venda (Fatura Recibo)"""
    funcionario = user.funcionario
    
    # Criar a venda
    venda = Venda.objects.create(
        empresa=proforma.empresa,
        loja=funcionario.loja_principal,
        cliente=proforma.cliente,
        vendedor=funcionario,
        forma_pagamento=FormaPagamento.objects.filter(
            empresa=proforma.empresa, 
            tipo='dinheiro', 
            ativa=True
        ).first(),
        subtotal=proforma.subtotal,
        desconto_valor=proforma.desconto_global,
        iva_valor=proforma.iva_valor,
        total=proforma.total,
        valor_pago=proforma.total,  # Assumindo pagamento à vista
        troco=Decimal('0.00'),
        status='finalizada',
        observacoes=f'Convertido da Proforma {proforma.numero_proforma}'
    )
    
    # Converter itens da proforma
    for item_proforma in proforma.itens.all():
        ItemVenda.objects.create(
            venda=venda,
            produto=item_proforma.produto,
            servico=item_proforma.servico,
            nome_produto=item_proforma.produto.nome_produto if item_proforma.produto else None,
            nome_servico=item_proforma.servico.nome if item_proforma.servico else None,
            quantidade=item_proforma.quantidade,
            preco_unitario=item_proforma.preco_unitario,
            desconto_item=item_proforma.desconto_item,
            subtotal_sem_iva=item_proforma.total - item_proforma.iva_valor,
            iva_percentual=item_proforma.iva_percentual,
            iva_valor=item_proforma.iva_valor,
            total=item_proforma.total
        )
        
        # Atualizar estoque se for produto
        if item_proforma.produto:
            item_proforma.produto.estoque_atual = F('estoque_atual') - item_proforma.quantidade
            item_proforma.produto.save(update_fields=['estoque_atual'])
    
    return venda

def _converter_para_fatura_credito(proforma, user):
    funcionario = request.user.funcionario
    if not funcionario.pode_realizar_acao('emitir_faturacredito'):
         return JsonResponse({'success': False, 'message': 'Você não tem permissão para emitir fatura crédito.'}, status=403)
    
    """Converte uma proforma em uma Fatura a Crédito"""
    
    # Criar a fatura a crédito (assumindo vencimento em 30 dias)
    data_vencimento = timezone.now().date() + timedelta(days=30)
    
    fatura_credito = FaturaCredito.objects.create(
        empresa=proforma.empresa,
        cliente=proforma.cliente,
        data_vencimento=data_vencimento,
        subtotal=proforma.subtotal,
        iva_valor=proforma.iva_valor,
        total_faturado=proforma.total,
        observacoes=f'Convertido da Proforma {proforma.numero_proforma}'
    )
    
    # Converter itens da proforma
    for item_proforma in proforma.itens.all():
        ItemFatura.objects.create(
            fatura=fatura_credito,
            produto=item_proforma.produto,
            servico=item_proforma.servico,
            nome_item=item_proforma.produto.nome_produto if item_proforma.produto else (
                item_proforma.servico.nome if item_proforma.servico else 'Item'
            ),
            quantidade=item_proforma.quantidade,
            preco_unitario=item_proforma.preco_unitario,
            desconto_item=item_proforma.desconto_item,
            subtotal=item_proforma.total - item_proforma.iva_valor,
            iva_percentual=item_proforma.iva_percentual,
            iva_valor=item_proforma.iva_valor,
            total=item_proforma.total
        )
    
    return fatura_credito

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def atualizar_status_proforma_api(request, proforma_id):
    """API para atualizar o status de uma Proforma"""
    try:
        data = json.loads(request.body)
        novo_status = data.get('status')
        
        # Verificar se o status é válido
        status_validos = ['emitida', 'aceite', 'rejeitada', 'convertida', 'expirado']
        if novo_status not in status_validos:
            return JsonResponse({'success': False, 'message': 'Status inválido'})
        
        # Obter a proforma
        proforma = get_object_or_404(FaturaProforma, id=proforma_id, empresa=request.user.empresa)
        
        # Atualizar status
        status_anterior = proforma.status
        proforma.status = novo_status
        proforma.save()
        
        status_nomes = {
            'emitida': 'Pendente',
            'aceite': 'Aceita',
            'rejeitada': 'Rejeitada',
            'convertida': 'Convertida',
            'expirado': 'Expirada'
        }
        
        return JsonResponse({
            'success': True,
            'message': f'Status alterado de {status_nomes.get(status_anterior, status_anterior)} para {status_nomes.get(novo_status, novo_status)}',
            'status_anterior': status_anterior,
            'status_novo': novo_status
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar status da proforma {proforma_id}: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erro ao atualizar status: {str(e)}'})



# =====================================
# NOTAS DE CRÉDITO
# =====================================

class NotaCreditoListView(BaseVendaView, ListView):
    model = NotaCredito
    template_name = 'vendas/nota_credito_lista.html'
    context_object_name = 'notas_credito'
    paginate_by = 20
    
    def get_queryset(self):
        empresa = self.get_empresa()
        queryset = NotaCredito.objects.filter(empresa=empresa)
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        motivo = self.request.GET.get('motivo')
        if motivo:
            queryset = queryset.filter(motivo=motivo)
        
        cliente_nome = self.request.GET.get('cliente')
        if cliente_nome:
            queryset = queryset.filter(
                Q(cliente__nome_completo__icontains=cliente_nome) |
                Q(cliente__nif__icontains=cliente_nome)
            )
        
        # Período
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_emissao__date__lte=data_fim)
        
        return queryset.select_related('cliente', 'vendedor').order_by('-data_emissao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Estatísticas
        stats = NotaCredito.objects.filter(empresa=empresa).aggregate(
            total_creditos=Sum('total_credito'),
            quantidade_total=Count('id'),
            pendentes_aprovacao=Count('id', filter=Q(requer_aprovacao=True, aprovada_por__isnull=True)),
            aplicadas=Count('id', filter=Q(status='aplicada'))
        )
        
        context.update({
            'title': 'Notas de Crédito',
            'stats': stats,
            'status_choices': NotaCredito.STATUS_CHOICES,
            'motivo_choices': NotaCredito.MOTIVO_CHOICES,
        })
        return context


class NotaCreditoDetailView(BaseVendaView, DetailView):
    model = NotaCredito
    template_name = 'vendas/nota_credito_detail.html'
    context_object_name = 'nota_credito'
    
    def get_queryset(self):
        return NotaCredito.objects.filter(empresa=self.get_empresa())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nota = self.get_object()
        
        context.update({
            'title': f'Nota de Crédito {nota.numero_nota}',
            'itens': nota.itens.select_related('produto', 'servico'),
            'pode_aplicar': nota.pode_ser_aplicada()[0],
            'motivo_nao_aplicar': nota.pode_ser_aplicada()[1],
        })
        return context


class NotaCreditoCreateView(PermissaoAcaoMixin, BaseVendaView, CreateView):
    acao_requerida = 'emitir_notacredito'
    
    model = NotaCredito
    form_class = NotaCreditoForm
    template_name = 'vendas/nota_credito_form.html'
    success_url = reverse_lazy('vendas:nota_credito_lista')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        form.instance.emitida_por = self.request.user
        
        # Se tem vendedor no usuário logado, usar como padrão
        if hasattr(self.request.user, 'funcionario'):
            form.instance.vendedor = self.request.user.funcionario
        
        messages.success(self.request, f'Nota de Crédito {form.instance.numero_nota} criada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Nova Nota de Crédito',
            'subtitle': 'Emitir documento de crédito para reduzir valor de fatura',
        })
        return context


class NotaCreditoUpdateView(PermissaoAcaoMixin, BaseVendaView, UpdateView):
    acao_requerida = 'emitir_notacredito'
    
    model = NotaCredito
    form_class = NotaCreditoForm
    template_name = 'vendas/nota_credito_form.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:nota_credito_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        return NotaCredito.objects.filter(empresa=self.get_empresa())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        if self.object.status not in ['rascunho', 'emitida']:
            messages.error(self.request, 'Não é possível editar esta nota de crédito.')
            return redirect(self.get_success_url())
        
        messages.success(self.request, 'Nota de Crédito atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Editar Nota de Crédito {self.object.numero_nota}',
            'subtitle': 'Modificar dados da nota de crédito',
        })
        return context


class AplicarNotaCreditoView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'aplicar_notacredito'
    
    def post(self, request, pk):
        nota = get_object_or_404(NotaCredito, pk=pk, empresa=self.get_empresa())
        
        try:
            with transaction.atomic():
                nota.aplicar_credito(request.user)
                messages.success(request, f'Nota de Crédito {nota.numero_nota} aplicada com sucesso!')
        except ValidationError as e:
            messages.error(request, f'Erro ao aplicar nota de crédito: {e}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
        
        return redirect('vendas:nota_credito_detail', pk=pk)


class AprovarNotaCreditoView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'aprovar_notacredito'
    
    def post(self, request, pk):
        nota = get_object_or_404(NotaCredito, pk=pk, empresa=self.get_empresa())
        
        if not nota.requer_aprovacao:
            messages.warning(request, 'Esta nota de crédito não requer aprovação.')
        elif nota.aprovada_por:
            messages.warning(request, 'Esta nota de crédito já foi aprovada.')
        else:
            nota.aprovada_por = request.user
            nota.data_aprovacao = timezone.now()
            nota.save()
            messages.success(request, f'Nota de Crédito {nota.numero_nota} aprovada com sucesso!')
        
        return redirect('vendas:nota_credito_detail', pk=pk)


# =====================================
# NOTAS DE DÉBITO
# =====================================

class NotaDebitoListView(BaseVendaView, ListView):
    model = NotaDebito
    template_name = 'vendas/nota_debito_lista.html'
    context_object_name = 'notas_debito'
    paginate_by = 20
    
    def get_queryset(self):
        empresa = self.get_empresa()
        queryset = NotaDebito.objects.filter(empresa=empresa)
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        motivo = self.request.GET.get('motivo')
        if motivo:
            queryset = queryset.filter(motivo=motivo)
        
        cliente_nome = self.request.GET.get('cliente')
        if cliente_nome:
            queryset = queryset.filter(
                Q(cliente__nome_completo__icontains=cliente_nome) |
                Q(cliente__nif__icontains=cliente_nome)
            )
        
        # Vencidas
        vencidas = self.request.GET.get('vencidas')
        if vencidas == '1':
            queryset = queryset.filter(
                data_vencimento__lt=timezone.now().date(),
                status__in=['emitida', 'aplicada']
            )
        
        return queryset.select_related('cliente', 'vendedor').order_by('-data_emissao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Estatísticas
        stats = NotaDebito.objects.filter(empresa=empresa).aggregate(
            total_debitos=Sum('total_debito'),
            total_pendente=Sum('total_debito', filter=Q(status__in=['emitida', 'aplicada'])) - Sum('valor_pago', filter=Q(status__in=['emitida', 'aplicada'])),
            quantidade_total=Count('id'),
            vencidas=Count('id', filter=Q(data_vencimento__lt=timezone.now().date(), status__in=['emitida', 'aplicada'])),
            aplicadas=Count('id', filter=Q(status='aplicada'))
        )
        
        context.update({
            'title': 'Notas de Débito',
            'stats': stats,
            'status_choices': NotaDebito.STATUS_CHOICES,
            'motivo_choices': NotaDebito.MOTIVO_CHOICES,
        })
        return context


class NotaDebitoDetailView(BaseVendaView, DetailView):
    model = NotaDebito
    template_name = 'vendas/nota_debito_detail.html'
    context_object_name = 'nota_debito'
    
    def get_queryset(self):
        return NotaDebito.objects.filter(empresa=self.get_empresa())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nota = self.get_object()
        
        # Verificar se está vencida
        esta_vencida = nota.data_vencimento < timezone.now().date()
        dias_para_vencimento = (nota.data_vencimento - timezone.now().date()).days
        
        context.update({
            'title': f'Nota de Débito {nota.numero_nota}',
            'itens': nota.itens.select_related('produto', 'servico'),
            'pode_aplicar': nota.pode_ser_aplicada()[0],
            'motivo_nao_aplicar': nota.pode_ser_aplicada()[1],
            'esta_vencida': esta_vencida,
            'dias_vencimento': dias_para_vencimento,
        })
        return context


class NotaDebitoCreateView(PermissaoAcaoMixin, BaseVendaView, CreateView):
    acao_requerida = 'emitir_notadebito'
    
    model = NotaDebito
    form_class = NotaDebitoForm
    template_name = 'vendas/nota_debito_form.html'
    success_url = reverse_lazy('vendas:nota_debito_lista')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        form.instance.emitida_por = self.request.user
        
        # Se tem vendedor no usuário logado, usar como padrão
        if hasattr(self.request.user, 'funcionario'):
            form.instance.vendedor = self.request.user.funcionario
        
        messages.success(self.request, f'Nota de Débito {form.instance.numero_nota} criada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Nova Nota de Débito',
            'subtitle': 'Emitir documento de débito para cobrança adicional',
        })
        return context


class NotaDebitoUpdateView(PermissaoAcaoMixin, BaseVendaView, UpdateView):
    acao_requerida = 'emitir_notadebito'
    
    model = NotaDebito
    form_class = NotaDebitoForm
    template_name = 'vendas/nota_debito_form.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:nota_debito_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        return NotaDebito.objects.filter(empresa=self.get_empresa())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        if self.object.status not in ['rascunho', 'emitida']:
            messages.error(self.request, 'Não é possível editar esta nota de débito.')
            return redirect(self.get_success_url())
        
        messages.success(self.request, 'Nota de Débito atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Editar Nota de Débito {self.object.numero_nota}',
            'subtitle': 'Modificar dados da nota de débito',
        })
        return context


class AplicarNotaDebitoView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'aplicar_notadebito'
    
    def post(self, request, pk):
        nota = get_object_or_404(NotaDebito, pk=pk, empresa=self.get_empresa())
        
        try:
            with transaction.atomic():
                nota.aplicar_debito(request.user)
                messages.success(request, f'Nota de Débito {nota.numero_nota} aplicada com sucesso!')
        except ValidationError as e:
            messages.error(request, f'Erro ao aplicar nota de débito: {e}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
        
        return redirect('vendas:nota_debito_detail', pk=pk)


class AprovarNotaDebitoView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'aprovar_notadebito'
    
    def post(self, request, pk):
        nota = get_object_or_404(NotaDebito, pk=pk, empresa=self.get_empresa())
        
        if not nota.requer_aprovacao:
            messages.warning(request, 'Esta nota de débito não requer aprovação.')
        elif nota.aprovada_por:
            messages.warning(request, 'Esta nota de débito já foi aprovada.')
        else:
            nota.aprovada_por = request.user
            nota.data_aprovacao = timezone.now()
            nota.save()
            messages.success(request, f'Nota de Débito {nota.numero_nota} aprovada com sucesso!')
        
        return redirect('vendas:nota_debito_detail', pk=pk)


# =====================================
# DOCUMENTOS DE TRANSPORTE
# =====================================

class DocumentoTransporteListView(BaseVendaView, ListView):
    model = DocumentoTransporte
    template_name = 'vendas/documento_transporte_lista.html'
    context_object_name = 'documentos_transporte'
    paginate_by = 20
    
    def get_queryset(self):
        empresa = self.get_empresa()
        queryset = DocumentoTransporte.objects.filter(empresa=empresa)
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        tipo_operacao = self.request.GET.get('tipo_operacao')
        if tipo_operacao:
            queryset = queryset.filter(tipo_operacao=tipo_operacao)
        
        destinatario = self.request.GET.get('destinatario')
        if destinatario:
            queryset = queryset.filter(
                Q(destinatario_nome__icontains=destinatario) |
                Q(destinatario_nif__icontains=destinatario)
            )
        
        # Atrasados
        atrasados = self.request.GET.get('atrasados')
        if atrasados == '1':
            queryset = queryset.filter(
                data_previsao_entrega__lt=timezone.now(),
                status__in=['preparando', 'em_transito']
            )
        
        return queryset.select_related('destinatario_cliente').order_by('-data_emissao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Estatísticas
        stats = DocumentoTransporte.objects.filter(empresa=empresa).aggregate(
            total_documentos=Count('id'),
            em_transito=Count('id', filter=Q(status='em_transito')),
            entregues=Count('id', filter=Q(status='entregue')),
            atrasados=Count('id', filter=Q(
                data_previsao_entrega__lt=timezone.now(),
                status__in=['preparando', 'em_transito']
            )),
            peso_total=Sum('peso_total'),
            valor_total_transportes=Sum('valor_transporte')
        )
        
        context.update({
            'title': 'Documentos de Transporte',
            'stats': stats,
            'status_choices': DocumentoTransporte.STATUS_CHOICES,
            'tipo_operacao_choices': DocumentoTransporte.TIPO_OPERACAO_CHOICES,
        })
        return context


class DocumentoTransporteDetailView(BaseVendaView, DetailView):
    model = DocumentoTransporte
    template_name = 'vendas/documento_transporte_detail.html'
    context_object_name = 'documento'
    
    def get_queryset(self):
        return DocumentoTransporte.objects.filter(empresa=self.get_empresa())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.get_object()
        
        # Cálculo do progresso
        itens = documento.itens.all()
        total_peso = sum(item.peso_total for item in itens)
        total_valor = sum(item.valor_total for item in itens)
        
        # Calcular tempo de transporte se já iniciado
        tempo_transporte = None
        if documento.data_inicio_transporte_real:
            if documento.data_entrega_real:
                tempo_transporte = documento.data_entrega_real - documento.data_inicio_transporte_real
            else:
                tempo_transporte = timezone.now() - documento.data_inicio_transporte_real
        
        context.update({
            'title': f'Documento de Transporte {documento.numero_documento}',
            'itens': itens,
            'total_peso_calculado': total_peso,
            'total_valor_calculado': total_valor,
            'pode_iniciar': documento.status == 'preparando',
            'pode_confirmar': documento.status == 'em_transito',
            'tempo_transporte': tempo_transporte,
        })
        return context


class DocumentoTransporteCreateView(PermissaoAcaoMixin, BaseVendaView, CreateView):
    acao_requerida = 'emitir_documentotransporte'
    
    model = DocumentoTransporte
    form_class = DocumentoTransporteForm
    template_name = 'vendas/documento_transporte_form.html'
    success_url = reverse_lazy('vendas:documento_transporte_lista')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        form.instance.emitido_por = self.request.user
        
        messages.success(self.request, f'Documento de Transporte {form.instance.numero_documento} criado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Novo Documento de Transporte',
            'subtitle': 'Criar guia de transporte para mercadorias',
        })
        return context


class DocumentoTransporteUpdateView(PermissaoAcaoMixin, BaseVendaView, UpdateView):
    acao_requerida = 'emitir_documentotransporte'
    
    model = DocumentoTransporte
    form_class = DocumentoTransporteForm
    template_name = 'vendas/documento_transporte_form.html'
    
    def get_success_url(self):
        return reverse_lazy('vendas:documento_transporte_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        return DocumentoTransporte.objects.filter(empresa=self.get_empresa())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        if self.object.status not in ['preparando']:
            messages.error(self.request, 'Só é possível editar documentos em preparação.')
            return redirect(self.get_success_url())
        
        messages.success(self.request, 'Documento de Transporte atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Editar Documento {self.object.numero_documento}',
            'subtitle': 'Modificar dados do documento de transporte',
        })
        return context


class IniciarTransporteView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'confirmar_entrega'
    
    def post(self, request, pk):
        documento = get_object_or_404(DocumentoTransporte, pk=pk, empresa=self.get_empresa())
        
        try:
            documento.iniciar_transporte()
            messages.success(request, f'Transporte {documento.numero_documento} iniciado com sucesso!')
        except ValidationError as e:
            messages.error(request, f'Erro ao iniciar transporte: {e}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
        
        return redirect('vendas:documento_transporte_detail', pk=pk)


class ConfirmarEntregaView(PermissaoAcaoMixin, BaseVendaView, View):
    acao_requerida = 'confirmar_entrega'
    
    def post(self, request, pk):
        documento = get_object_or_404(DocumentoTransporte, pk=pk, empresa=self.get_empresa())
        assinatura = request.POST.get('assinatura_destinatario', '')
        
        try:
            documento.confirmar_entrega(request.user, assinatura)
            messages.success(request, f'Entrega do documento {documento.numero_documento} confirmada com sucesso!')
        except ValidationError as e:
            messages.error(request, f'Erro ao confirmar entrega: {e}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')
        
        return redirect('vendas:documento_transporte_detail', pk=pk)


# =====================================
# DASHBOARDS E RELATÓRIOS
# =====================================

class DocumentosFiscaisAnalyticsView(BaseVendaView, TemplateView):
    template_name = 'vendas/documentos_fiscais_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Período para análise
        periodo = self.request.GET.get('periodo', '30')
        data_inicio = timezone.now().date() - timedelta(days=int(periodo))
        
        # Estatísticas de Notas de Crédito
        nc_stats = NotaCredito.objects.filter(
            empresa=empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_nc=Count('id'),
            valor_total_nc=Sum('total_credito'),
            aplicadas=Count('id', filter=Q(status='aplicada')),
            pendentes_aprovacao=Count('id', filter=Q(requer_aprovacao=True, aprovada_por__isnull=True))
        )
        
        # Estatísticas de Notas de Débito
        nd_stats = NotaDebito.objects.filter(
            empresa=empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_nd=Count('id'),
            valor_total_nd=Sum('total_debito'),
            valor_pago_nd=Sum('valor_pago'),
            aplicadas=Count('id', filter=Q(status='aplicada')),
            vencidas=Count('id', filter=Q(data_vencimento__lt=timezone.now().date()))
        )
        
        # Estatísticas de Documentos de Transporte
        gt_stats = DocumentoTransporte.objects.filter(
            empresa=empresa,
            data_emissao__gte=data_inicio
        ).aggregate(
            total_gt=Count('id'),
            em_transito=Count('id', filter=Q(status='em_transito')),
            entregues=Count('id', filter=Q(status='entregue')),
            atrasados=Count('id', filter=Q(
                data_previsao_entrega__lt=timezone.now(),
                status__in=['preparando', 'em_transito']
            )),
            peso_total=Sum('peso_total'),
            valor_transportes=Sum('valor_transporte')
        )
        
        # Notas de Crédito por motivo
        nc_por_motivo = NotaCredito.objects.filter(
            empresa=empresa,
            data_emissao__gte=data_inicio
        ).values('motivo').annotate(
            quantidade=Count('id'),
            valor_total=Sum('total_credito')
        ).order_by('-valor_total')
        
        # Documentos de transporte por status
        gt_por_status = DocumentoTransporte.objects.filter(
            empresa=empresa,
            data_emissao__gte=data_inicio
        ).values('status').annotate(
            quantidade=Count('id')
        )
        
        context.update({
            'title': 'Analytics de Documentos Fiscais',
            'periodo': periodo,
            'data_inicio': data_inicio,
            'nc_stats': nc_stats,
            'nd_stats': nd_stats,
            'gt_stats': gt_stats,
            'nc_por_motivo': nc_por_motivo,
            'gt_por_status': gt_por_status,
        })
        return context


class RelatorioNotasCreditoView(BaseVendaView, TemplateView):
    template_name = 'vendas/relatorio_notas_credito.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Filtros
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        cliente_id = self.request.GET.get('cliente_id')
        motivo = self.request.GET.get('motivo')
        
        # Query base
        queryset = NotaCredito.objects.filter(empresa=empresa)
        
        if data_inicio:
            queryset = queryset.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_emissao__date__lte=data_fim)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if motivo:
            queryset = queryset.filter(motivo=motivo)
        
        # Agregações
        totais = queryset.aggregate(
            total_creditos=Sum('total_credito'),
            quantidade=Count('id'),
            credito_medio=Avg('total_credito')
        )
        
        # Agrupamentos
        por_cliente = queryset.values(
            'cliente__nome_completo'
        ).annotate(
            total=Sum('total_credito'),
            quantidade=Count('id')
        ).order_by('-total')[:10]
        
        por_motivo = queryset.values('motivo').annotate(
            total=Sum('total_credito'),
            quantidade=Count('id')
        ).order_by('-total')
        
        context.update({
            'title': 'Relatório de Notas de Crédito',
            'notas_credito': queryset.select_related('cliente')[:100],
            'totais': totais,
            'por_cliente': por_cliente,
            'por_motivo': por_motivo,
            'clientes': Cliente.objects.filter(empresa=empresa, ativo=True),
            'motivo_choices': NotaCredito.MOTIVO_CHOICES,
        })
        return context


class RelatorioTransportesView(BaseVendaView, TemplateView):
    template_name = 'vendas/relatorio_transportes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.get_empresa()
        
        # Filtros
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        status = self.request.GET.get('status')
        provincia = self.request.GET.get('provincia')
        
        # Query base
        queryset = DocumentoTransporte.objects.filter(empresa=empresa)
        
        if data_inicio:
            queryset = queryset.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_emissao__date__lte=data_fim)
        if status:
            queryset = queryset.filter(status=status)
        if provincia:
            queryset = queryset.filter(destinatario_provincia=provincia)
        
        # Agregações
        totais = queryset.aggregate(
            total_documentos=Count('id'),
            peso_total=Sum('peso_total'),
            valor_total=Sum('valor_transporte'),
            valor_medio=Avg('valor_transporte')
        )
        
        # Performance de entregas
        entregues = queryset.filter(status='entregue', data_entrega_real__isnull=False)
        entregas_no_prazo = 0
        entregas_atrasadas = 0
        
        for doc in entregues:
            if doc.data_entrega_real.date() <= doc.data_previsao_entrega:
                entregas_no_prazo += 1
            else:
                entregas_atrasadas += 1
        
        # Por província
        por_provincia = queryset.values('destinatario_provincia').annotate(
            total=Count('id'),
            peso=Sum('peso_total'),
            valor=Sum('valor_transporte')
        ).order_by('-total')
        
        context.update({
            'title': 'Relatório de Transportes',
            'documentos': queryset.select_related('destinatario_cliente')[:100],
            'totais': totais,
            'entregas_no_prazo': entregas_no_prazo,
            'entregas_atrasadas': entregas_atrasadas,
            'por_provincia': por_provincia,
            'status_choices': DocumentoTransporte.STATUS_CHOICES,
        })
        return context


# =====================================
# APIs E UTILITÁRIOS
# =====================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def finalizar_nota_credito_api(request):
    """API para finalizar criação de Nota de Crédito com itens"""
    try:
        funcionario = getattr(request.user, 'funcionario', None)
        if not funcionario or not funcionario.pode_realizar_acao('emitir_notacredito'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir notas de crédito.'
            }, status=403)
    except AttributeError:
        # Se não tem sistema de funcionários, verificar permissão simples
        if not request.user.has_perm('vendas.add_notacredito'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir notas de crédito.'
            }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        required_fields = ['cliente_id', 'motivo', 'total_credito']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False, 
                'message': 'Campos obrigatórios ausentes.'
            }, status=400)
        
        with transaction.atomic():
            # Criar Nota de Crédito
            nota_data = {
                'empresa': request.user.empresa,
                'cliente_id': data['cliente_id'],
                'motivo': data['motivo'],
                'descricao_motivo': data.get('descricao_motivo', ''),
                'total_credito': Decimal(str(data['total_credito'])),
                'observacoes': data.get('observacoes', ''),
                'emitida_por': request.user
            }
            
            # Documentos de origem opcionais
            if data.get('venda_origem_id'):
                nota_data['venda_origem_id'] = data['venda_origem_id']
            if data.get('fatura_credito_origem_id'):
                nota_data['fatura_credito_origem_id'] = data['fatura_credito_origem_id']
            
            nota_credito = NotaCredito.objects.create(**nota_data)
            
            # Criar itens
            for item_data in data.get('itens', []):
                ItemNotaCredito.objects.create(
                    nota_credito=nota_credito,
                    produto_id=item_data.get('produto_id'),
                    servico_id=item_data.get('servico_id'),
                    descricao_item=item_data['descricao_item'],
                    quantidade_creditada=Decimal(str(item_data['quantidade_creditada'])),
                    valor_unitario_credito=Decimal(str(item_data['valor_unitario_credito'])),
                    iva_percentual=Decimal(str(item_data.get('iva_percentual', 14))),
                    motivo_item=item_data.get('motivo_item', '')
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Nota de Crédito criada com sucesso!',
            'nota_id': nota_credito.id,
            'numero_nota': nota_credito.numero_nota
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar nota de crédito: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def finalizar_nota_debito_api(request):
    """API para finalizar criação de Nota de Débito com itens"""
    try:
        funcionario = getattr(request.user, 'funcionario', None)
        if not funcionario or not funcionario.pode_realizar_acao('emitir_notadebito'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir notas de débito.'
            }, status=403)
    except AttributeError:
        if not request.user.has_perm('vendas.add_notadebito'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir notas de débito.'
            }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        required_fields = ['cliente_id', 'motivo', 'total_debito', 'data_vencimento']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False, 
                'message': 'Campos obrigatórios ausentes.'
            }, status=400)
        
        with transaction.atomic():
            # Criar Nota de Débito
            nota_data = {
                'empresa': request.user.empresa,
                'cliente_id': data['cliente_id'],
                'motivo': data['motivo'],
                'descricao_motivo': data.get('descricao_motivo', ''),
                'data_vencimento': datetime.strptime(data['data_vencimento'], '%Y-%m-%d').date(),
                'total_debito': Decimal(str(data['total_debito'])),
                'observacoes': data.get('observacoes', ''),
                'emitida_por': request.user
            }
            
            # Documentos de origem opcionais
            if data.get('venda_origem_id'):
                nota_data['venda_origem_id'] = data['venda_origem_id']
            if data.get('fatura_credito_origem_id'):
                nota_data['fatura_credito_origem_id'] = data['fatura_credito_origem_id']
            
            nota_debito = NotaDebito.objects.create(**nota_data)
            
            # Criar itens
            for item_data in data.get('itens', []):
                ItemNotaDebito.objects.create(
                    nota_debito=nota_debito,
                    produto_id=item_data.get('produto_id'),
                    servico_id=item_data.get('servico_id'),
                    descricao_item=item_data['descricao_item'],
                    quantidade=Decimal(str(item_data['quantidade'])),
                    valor_unitario=Decimal(str(item_data['valor_unitario'])),
                    iva_percentual=Decimal(str(item_data.get('iva_percentual', 14))),
                    justificativa=item_data.get('justificativa', '')
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Nota de Débito criada com sucesso!',
            'nota_id': nota_debito.id,
            'numero_nota': nota_debito.numero_nota
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar nota de débito: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def finalizar_documento_transporte_api(request):
    """API para finalizar criação de Documento de Transporte com itens"""
    try:
        funcionario = getattr(request.user, 'funcionario', None)
        if not funcionario or not funcionario.pode_realizar_acao('emitir_documentotransporte'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir documentos de transporte.'
            }, status=403)
    except AttributeError:
        if not request.user.has_perm('vendas.add_documentotransporte'):
            return JsonResponse({
                'success': False, 
                'message': 'Sem permissão para emitir documentos de transporte.'
            }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validações básicas
        required_fields = ['destinatario_nome', 'destinatario_endereco', 'data_inicio_transporte', 'data_previsao_entrega']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False, 
                'message': 'Campos obrigatórios ausentes.'
            }, status=400)
        
        with transaction.atomic():
            # Criar Documento de Transporte
            documento_data = {
                'empresa': request.user.empresa,
                'tipo_operacao': data.get('tipo_operacao', 'venda'),
                'tipo_transporte': data.get('tipo_transporte', 'proprio'),
                'data_inicio_transporte': datetime.strptime(data['data_inicio_transporte'], '%Y-%m-%d').date(),
                'data_previsao_entrega': datetime.strptime(data['data_previsao_entrega'], '%Y-%m-%d').date(),
                'destinatario_nome': data['destinatario_nome'],
                'destinatario_endereco': data['destinatario_endereco'],
                'destinatario_telefone': data.get('destinatario_telefone', ''),
                'destinatario_provincia': data.get('destinatario_provincia', ''),
                'destinatario_nif': data.get('destinatario_nif', ''),
                'transportador_nome': data.get('transportador_nome', ''),
                'veiculo_matricula': data.get('veiculo_matricula', ''),
                'condutor_nome': data.get('condutor_nome', ''),
                'valor_transporte': Decimal(str(data.get('valor_transporte', 0))),
                'observacoes': data.get('observacoes', ''),
                'emitido_por': request.user
            }
            
            # Documentos de origem opcionais
            if data.get('venda_origem_id'):
                documento_data['venda_origem_id'] = data['venda_origem_id']
            if data.get('fatura_credito_origem_id'):
                documento_data['fatura_credito_origem_id'] = data['fatura_credito_origem_id']
            if data.get('destinatario_cliente_id'):
                documento_data['destinatario_cliente_id'] = data['destinatario_cliente_id']
            
            documento = DocumentoTransporte.objects.create(**documento_data)
            
            # Criar itens
            peso_total = Decimal('0.000')
            for item_data in data.get('itens', []):
                item = ItemDocumentoTransporte.objects.create(
                    documento=documento,
                    produto_id=item_data.get('produto_id'),
                    codigo_produto=item_data.get('codigo_produto', ''),
                    descricao_produto=item_data['descricao_produto'],
                    quantidade_enviada=Decimal(str(item_data['quantidade_enviada'])),
                    peso_unitario=Decimal(str(item_data.get('peso_unitario', 0))),
                    valor_unitario=Decimal(str(item_data.get('valor_unitario', 0))),
                    tipo_embalagem=item_data.get('tipo_embalagem', ''),
                    observacoes_item=item_data.get('observacoes_item', '')
                )
                peso_total += item.peso_total
            
            # Atualizar peso total do documento
            documento.peso_total = peso_total
            documento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Documento de Transporte criado com sucesso!',
            'documento_id': documento.id,
            'numero_documento': documento.numero_documento
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar documento de transporte: {str(e)}'
        }, status=500)


@login_required
def buscar_documentos_origem_api(request):
    """API para buscar documentos de origem para notas de crédito/débito"""
    try:
        tipo = request.GET.get('tipo')  # 'venda' ou 'fatura_credito'
        termo = request.GET.get('termo', '')
        empresa = request.user.empresa
        
        resultados = []
        
        if tipo == 'venda':
            vendas = Venda.objects.filter(
                empresa=empresa,
                status='finalizada'
            )
            if termo:
                vendas = vendas.filter(
                    Q(numero_venda__icontains=termo) |
                    Q(cliente__nome_completo__icontains=termo)
                )
            
            for venda in vendas[:20]:
                resultados.append({
                    'id': venda.id,
                    'numero': venda.numero_venda,
                    'cliente': venda.cliente.nome_completo if venda.cliente else 'N/A',
                    'data': venda.data_venda.strftime('%d/%m/%Y'),
                    'total': float(venda.total)
                })
        
        elif tipo == 'fatura_credito':
            # Buscar faturas do módulo de faturas se existir
            try:
                from apps.vendas.models import FaturaCredito
                faturas = FaturaCredito.objects.filter(empresa=empresa)
                if termo:
                    faturas = faturas.filter(
                        Q(numero_fatura__icontains=termo) |
                        Q(cliente__nome_completo__icontains=termo)
                    )
                
                for fatura in faturas[:20]:
                    resultados.append({
                        'id': fatura.id,
                        'numero': fatura.numero_fatura,
                        'cliente': fatura.cliente.nome_completo,
                        'data': fatura.data_emissao.strftime('%d/%m/%Y'),
                        'total': float(fatura.total_faturado)
                    })
            except ImportError:
                # Se módulo de faturas não existe, usar vendas a crédito
                vendas = Venda.objects.filter(
                    empresa=empresa,
                    forma_pagamento='credito'
                )
                if termo:
                    vendas = vendas.filter(
                        Q(numero_venda__icontains=termo) |
                        Q(cliente__nome_completo__icontains=termo)
                    )
                
                for venda in vendas[:20]:
                    resultados.append({
                        'id': venda.id,
                        'numero': venda.numero_venda,
                        'cliente': venda.cliente.nome_completo if venda.cliente else 'N/A',
                        'data': venda.data_venda.strftime('%d/%m/%Y'),
                        'total': float(venda.total)
                    })
        
        return JsonResponse({'success': True, 'documentos': resultados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# =====================================
# VIEWS DE PDF
# =====================================

@require_GET
@login_required
def nota_credito_pdf_view(request, nota_id):
    """Gera PDF da Nota de Crédito"""
    try:
        # Verificar permissão
        if not request.user.has_perm('vendas.view_notacredito'):
            raise Http404("Sem permissão para visualizar este documento")
        
        nota = get_object_or_404(
            NotaCredito.objects.select_related(
                'empresa', 'cliente'
            ).prefetch_related('itens'),
            pk=nota_id,
            empresa=request.user.empresa
        )
        
        # Preparar contexto
        context = {
            'nota': nota,
            'empresa': nota.empresa,
            'cliente': nota.cliente,
            'itens': nota.itens.all(),
            'request': request,
        }
        
        # Tentar usar WeasyPrint ou fallback para HTML
        try:
            from weasyprint import HTML
            html_string = render_to_string('vendas/pdfs/nota_credito_pdf.html', context)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Nota_Credito_{nota.numero_nota}.pdf"'
            return response
        except ImportError:
            # Fallback para HTML se WeasyPrint não estiver disponível
            html_string = render_to_string('vendas/pdfs/nota_credito_pdf.html', context)
            response = HttpResponse(html_string, content_type='text/html')
            return response
            
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('vendas:nota_credito_detail', pk=nota_id)


@require_GET
@login_required
def nota_debito_pdf_view(request, nota_id):
    """Gera PDF da Nota de Débito"""
    try:
        if not request.user.has_perm('vendas.view_notadebito'):
            raise Http404("Sem permissão para visualizar este documento")
        
        nota = get_object_or_404(
            NotaDebito.objects.select_related(
                'empresa', 'cliente'
            ).prefetch_related('itens'),
            pk=nota_id,
            empresa=request.user.empresa
        )
        
        context = {
            'nota': nota,
            'empresa': nota.empresa,
            'cliente': nota.cliente,
            'itens': nota.itens.all(),
            'request': request,
        }
        
        try:
            from weasyprint import HTML
            html_string = render_to_string('vendas/pdfs/nota_debito_pdf.html', context)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Nota_Debito_{nota.numero_nota}.pdf"'
            return response
        except ImportError:
            html_string = render_to_string('vendas/pdfs/nota_debito_pdf.html', context)
            response = HttpResponse(html_string, content_type='text/html')
            return response
            
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('vendas:nota_debito_detail', pk=nota_id)


@require_GET
@login_required
def documento_transporte_pdf_view(request, documento_id):
    """Gera PDF do Documento de Transporte"""
    try:
        if not request.user.has_perm('vendas.view_documentotransporte'):
            raise Http404("Sem permissão para visualizar este documento")
        
        documento = get_object_or_404(
            DocumentoTransporte.objects.select_related(
                'empresa', 'destinatario_cliente'
            ).prefetch_related('itens'),
            pk=documento_id,
            empresa=request.user.empresa
        )
        
        context = {
            'documento': documento,
            'empresa': documento.empresa,
            'itens': documento.itens.all(),
            'request': request,
        }
        
        try:
            from weasyprint import HTML
            html_string = render_to_string('vendas/pdfs/documento_transporte_pdf.html', context)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Documento_Transporte_{documento.numero_documento}.pdf"'
            return response
        except ImportError:
            html_string = render_to_string('vendas/pdfs/documento_transporte_pdf.html', context)
            response = HttpResponse(html_string, content_type='text/html')
            return response
            
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('vendas:documento_transporte_detail', pk=documento_id)


# =====================================
# VIEWS AJAX PARA GESTÃO DE ITENS
# =====================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def adicionar_item_nota_credito_api(request):
    """API para adicionar item à nota de crédito via AJAX"""
    try:
        data = json.loads(request.body)
        nota_id = data.get('nota_id')
        
        nota = get_object_or_404(NotaCredito, pk=nota_id, empresa=request.user.empresa)
        
        if nota.status not in ['rascunho', 'emitida']:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível adicionar itens a esta nota.'
            }, status=400)
        
        # Criar item
        item = ItemNotaCredito.objects.create(
            nota_credito=nota,
            produto_id=data.get('produto_id'),
            servico_id=data.get('servico_id'),
            descricao_item=data['descricao_item'],
            quantidade_creditada=Decimal(str(data['quantidade_creditada'])),
            valor_unitario_credito=Decimal(str(data['valor_unitario_credito'])),
            iva_percentual=Decimal(str(data.get('iva_percentual', 14))),
            motivo_item=data.get('motivo_item', '')
        )
        
        # Recalcular total da nota
        nota.recalcular_total()
        
        return JsonResponse({
            'success': True,
            'message': 'Item adicionado com sucesso!',
            'item_id': item.id,
            'novo_total': float(nota.total_credito)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar item: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def adicionar_item_nota_debito_api(request):
    """API para adicionar item à nota de débito via AJAX"""
    try:
        data = json.loads(request.body)
        nota_id = data.get('nota_id')
        
        nota = get_object_or_404(NotaDebito, pk=nota_id, empresa=request.user.empresa)
        
        if nota.status not in ['rascunho', 'emitida']:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível adicionar itens a esta nota.'
            }, status=400)
        
        # Criar item
        item = ItemNotaDebito.objects.create(
            nota_debito=nota,
            produto_id=data.get('produto_id'),
            servico_id=data.get('servico_id'),
            descricao_item=data['descricao_item'],
            quantidade=Decimal(str(data['quantidade'])),
            valor_unitario=Decimal(str(data['valor_unitario'])),
            iva_percentual=Decimal(str(data.get('iva_percentual', 14))),
            justificativa=data.get('justificativa', '')
        )
        
        # Recalcular total da nota
        nota.recalcular_total()
        
        return JsonResponse({
            'success': True,
            'message': 'Item adicionado com sucesso!',
            'item_id': item.id,
            'novo_total': float(nota.total_debito)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar item: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def adicionar_item_documento_transporte_api(request):
    """API para adicionar item ao documento de transporte via AJAX"""
    try:
        data = json.loads(request.body)
        documento_id = data.get('documento_id')
        
        documento = get_object_or_404(DocumentoTransporte, pk=documento_id, empresa=request.user.empresa)
        
        if documento.status != 'preparando':
            return JsonResponse({
                'success': False,
                'message': 'Não é possível adicionar itens a este documento.'
            }, status=400)
        
        # Criar item
        item = ItemDocumentoTransporte.objects.create(
            documento=documento,
            produto_id=data.get('produto_id'),
            codigo_produto=data.get('codigo_produto', ''),
            descricao_produto=data['descricao_produto'],
            quantidade_enviada=Decimal(str(data['quantidade_enviada'])),
            peso_unitario=Decimal(str(data.get('peso_unitario', 0))),
            valor_unitario=Decimal(str(data.get('valor_unitario', 0))),
            tipo_embalagem=data.get('tipo_embalagem', ''),
            observacoes_item=data.get('observacoes_item', '')
        )
        
        # Recalcular peso total do documento
        peso_total = sum(i.peso_total for i in documento.itens.all())
        documento.peso_total = peso_total
        documento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Item adicionado com sucesso!',
            'item_id': item.id,
            'novo_peso_total': float(documento.peso_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar item: {str(e)}'
        }, status=500)


# =====================================
# API PARA BUSCAR PRODUTOS E CLIENTES
# =====================================

@login_required
def buscar_produtos_api(request):
    """API para buscar produtos por termo de pesquisa"""
    try:
        termo = request.GET.get('termo', '')
        empresa = request.user.empresa
        
        produtos = Produto.objects.filter(
            empresa=empresa,
            ativo=True
        )
        
        if termo:
            produtos = produtos.filter(
                Q(nome__icontains=termo) |
                Q(codigo__icontains=termo)
            )
        
        resultados = []
        for produto in produtos[:20]:
            resultados.append({
                'id': produto.id,
                'codigo': produto.codigo,
                'nome': produto.nome,
                'preco_venda': float(produto.preco_venda),
                'peso': float(getattr(produto, 'peso', 0)),
                'unidade': getattr(produto, 'unidade', 'un')
            })
        
        return JsonResponse({'success': True, 'produtos': resultados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def buscar_servicos_api(request):
    """API para buscar serviços por termo de pesquisa"""
    try:
        termo = request.GET.get('termo', '')
        empresa = request.user.empresa
        
        servicos = Servico.objects.filter(
            empresa=empresa,
            ativo=True
        )
        
        if termo:
            servicos = servicos.filter(
                Q(nome__icontains=termo) |
                Q(codigo__icontains=termo)
            )
        
        resultados = []
        for servico in servicos[:20]:
            resultados.append({
                'id': servico.id,
                'codigo': servico.codigo,
                'nome': servico.nome,
                'preco': float(servico.preco),
                'unidade': getattr(servico, 'unidade', 'un')
            })
        
        return JsonResponse({'success': True, 'servicos': resultados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def buscar_clientes_api(request):
    """API para buscar clientes por termo de pesquisa"""
    try:
        termo = request.GET.get('termo', '')
        empresa = request.user.empresa
        
        clientes = Cliente.objects.filter(
            empresa=empresa,
            ativo=True
        )
        
        if termo:
            clientes = clientes.filter(
                Q(nome_completo__icontains=termo) |
                Q(nif__icontains=termo) |
                Q(email__icontains=termo)
            )
        
        resultados = []
        for cliente in clientes[:20]:
            resultados.append({
                'id': cliente.id,
                'nome_completo': cliente.nome_completo,
                'nif': cliente.nif,
                'email': cliente.email,
                'telefone': getattr(cliente, 'telefone', ''),
                'endereco': getattr(cliente, 'endereco', '')
            })
        
        return JsonResponse({'success': True, 'clientes': resultados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# =====================================
# VIEWS PARA EXCLUIR ITENS
# =====================================

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def remover_item_nota_credito_api(request, item_id):
    """API para remover item de nota de crédito"""
    try:
        item = get_object_or_404(ItemNotaCredito, pk=item_id)
        nota = item.nota_credito
        
        # Verificar permissão e empresa
        if nota.empresa != request.user.empresa:
            return JsonResponse({'success': False, 'message': 'Sem permissão.'}, status=403)
        
        if nota.status not in ['rascunho', 'emitida']:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível remover itens desta nota.'
            }, status=400)
        
        item.delete()
        nota.recalcular_total()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removido com sucesso!',
            'novo_total': float(nota.total_credito)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover item: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def remover_item_nota_debito_api(request, item_id):
    """API para remover item de nota de débito"""
    try:
        item = get_object_or_404(ItemNotaDebito, pk=item_id)
        nota = item.nota_debito
        
        # Verificar permissão e empresa
        if nota.empresa != request.user.empresa:
            return JsonResponse({'success': False, 'message': 'Sem permissão.'}, status=403)
        
        if nota.status not in ['rascunho', 'emitida']:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível remover itens desta nota.'
            }, status=400)
        
        item.delete()
        nota.recalcular_total()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removido com sucesso!',
            'novo_total': float(nota.total_debito)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover item: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def remover_item_documento_transporte_api(request, item_id):
    """API para remover item de documento de transporte"""
    try:
        item = get_object_or_404(ItemDocumentoTransporte, pk=item_id)
        documento = item.documento
        
        # Verificar permissão e empresa
        if documento.empresa != request.user.empresa:
            return JsonResponse({'success': False, 'message': 'Sem permissão.'}, status=403)
        
        if documento.status != 'preparando':
            return JsonResponse({
                'success': False,
                'message': 'Não é possível remover itens deste documento.'
            }, status=400)
        
        item.delete()
        
        # Recalcular peso total
        peso_total = sum(i.peso_total for i in documento.itens.all())
        documento.peso_total = peso_total
        documento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removido com sucesso!',
            'novo_peso_total': float(documento.peso_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover item: {str(e)}'
        }, status=500)


# =====================================
# VIEWS PARA ESTADÍSTICAS RÁPIDAS
# =====================================

@login_required
def estatisticas_rapidas_api(request):
    """API para obter estatísticas rápidas dos documentos"""
    try:
        empresa = request.user.empresa
        hoje = timezone.now().date()
        
        # Notas de Crédito
        nc_hoje = NotaCredito.objects.filter(
            empresa=empresa,
            data_emissao__date=hoje
        ).aggregate(
            quantidade=Count('id'),
            valor_total=Sum('total_credito')
        )
        
        # Notas de Débito
        nd_hoje = NotaDebito.objects.filter(
            empresa=empresa,
            data_emissao__date=hoje
        ).aggregate(
            quantidade=Count('id'),
            valor_total=Sum('total_debito')
        )
        
        # Documentos de Transporte
        gt_hoje = DocumentoTransporte.objects.filter(
            empresa=empresa,
            data_emissao__date=hoje
        ).aggregate(
            quantidade=Count('id'),
            em_transito=Count('id', filter=Q(status='em_transito'))
        )
        
        # Pendências
        pendencias = {
            'nc_pendentes_aprovacao': NotaCredito.objects.filter(
                empresa=empresa,
                requer_aprovacao=True,
                aprovada_por__isnull=True
            ).count(),
            'nd_vencidas': NotaDebito.objects.filter(
                empresa=empresa,
                data_vencimento__lt=hoje,
                status__in=['emitida', 'aplicada']
            ).count(),
            'transportes_atrasados': DocumentoTransporte.objects.filter(
                empresa=empresa,
                data_previsao_entrega__lt=hoje,
                status__in=['preparando', 'em_transito']
            ).count()
        }
        
        return JsonResponse({
            'success': True,
            'nc_hoje': nc_hoje,
            'nd_hoje': nd_hoje,
            'gt_hoje': gt_hoje,
            'pendencias': pendencias
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# apps/vendas/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from apps.vendas.models import Venda


class VendaViewSet(viewsets.ModelViewSet):
    """
    API Endpoints para gestão de Vendas/Documentos Fiscais.
    A criação de uma Venda dispara a lógica de HASH e ATCUD.
    """
    queryset = Venda.objects.all().order_by('-data_venda')
    serializer_class = VendaSerializer
    permission_classes = [permissions.IsAuthenticated] # Ajuste as permissões conforme a sua lógica

    def get_queryset(self):
        # Filtro de segurança: apenas vendas da empresa do utilizador
        user = self.request.user
        if user.is_staff: # Exemplo simples, ajuste para a sua modelagem de Funcionario/Empresa
            return self.queryset.filter(empresa=user.empresa) 
        return Venda.objects.none() # Ou a lógica de filtragem adequada

    def create(self, request, *args, **kwargs):
        """Método de criação otimizado que delega a lógica crítica ao Serializer."""
        # Note que o Serializer trata de tudo: validação, cálculo, criação de linhas e assinatura fiscal.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            "message": "Venda registrada e assinada fiscalmente com sucesso.",
            "documento": serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)



bi_cache = caches["B_I"]
class VendaCreateAPIView(generics.CreateAPIView):
    """
    Endpoint para criar uma nova venda e gerar o documento fiscal (HASH, ATCUD).
    Esta API é chamada pelo JavaScript do frontend (venda_form.html).
    """
    # Use o Serializer que criámos anteriormente que contém a lógica fiscal
    serializer_class = VendaSerializer 
    # queryset = Venda.objects.all() # Não estritamente necessário para Create

    def perform_create(self, serializer):
        # Transação garante atomicidade: se algo falhar (DB ou fiscal), tudo reverte.
        with transaction.atomic():
            # A lógica de cálculo de HASH, ATCUD e salvamento está no Serializer.create()
            venda_instance = serializer.save()
            return venda_instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer) 
            
            # Disparo Assíncrono da Análise de Margem (Integração Celery)
            verificar_margem_critica.delay() 
            
            headers = self.get_success_headers(serializer.data)
            # Retorna os dados CRÍTICOS (HASH e ATCUD) para o frontend exibir
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            # 🛑 Lógica de ALERTA CRÍTICO DE FALHA FISCAL/DB (Conforme a última proposta)
            assunto = "🚨 FALHA CRÍTICA NA TRANSAÇÃO FISCAL"
            # ... (Lógica de alerta por email/Slack) ...
            print(f"ALERTE DE FALHA ENVIADO: {assunto} - {e}")
            
            return Response(
                {"message": "Erro de processamento interno. O administrador foi alertado.", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # 1. Criação da Venda e Lógica Fiscal
                self.perform_create(serializer) 
                
                # 2. Disparar Tarefas Assíncronas (Alertas)
                verificar_margem_critica.delay() 
                
                # 🛑 3. INVALICAÇÃO INTELIGENTE DE CACHE (CRÍTICO PARA B.I.)
                # Limpa TODA a cache de B.I., forçando o Dashboard a recalcular.
                bi_cache.clear() 
                print("CACHE DE B.I. INVALIDADA: Nova venda registrada. Forçando recálculo do Dashboard.")
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            # ... (Lógica de Alerta de Falha Fiscal/DB) ...
            
            return Response(
                {"message": "Erro de processamento interno. O administrador foi alertado.", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# apps/vendas/views.py (ADAPTAÇÃO DA RentabilidadeAPIView)
from django.db.models import Sum, F, DecimalField
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import caches # Importar o módulo de cache


bi_cache = caches['B.I.'] 

class RentabilidadeAPIView(APIView):
    """
    Endpoint de Rentabilidade com camada de Caching Redis.
    """
    
    # TTL (Time To Live): 1 hora = 3600 segundos. Suficiente para B.I.
    CACHE_TTL = 60 * 60 

    def get(self, request, *args, **kwargs):
        data_inicio = request.query_params.get('data_inicio', 'all')
        data_fim = request.query_params.get('data_fim', 'all')
        
        # 1. Geração da Chave Única de Cache
        # A chave DEVE incluir os filtros de data para evitar cache de dados errados.
        cache_key = f"bi_rentabilidade_{data_inicio}_{data_fim}"
        
        # 2. TENTATIVA DE RECUPERAR DADOS DO CACHE
        dados_cache = bi_cache.get(cache_key)
        
        if dados_cache:
            # Hit de Cache: Resposta RÁPIDA (Não toca no DB)
            print(f"CACHE HIT: Servindo dados de Rentabilidade da chave {cache_key}")
            return Response(dados_cache)

        # 3. Cache Miss: Executar CÁLCULOS PESADOS NO DB
        print(f"CACHE MISS: A calcular dados de Rentabilidade e a gravar cache.")
        
        filtros = {}
        if data_inicio != 'all':
            filtros['venda__data_venda__gte'] = data_inicio
        if data_fim != 'all':
            filtros['venda__data_venda__lte'] = data_fim

        # Lógica de Agregação (A mesma lógica de cálculo pesado de Margem Bruta)
        resultados = VendaItem.objects.filter(**filtros).select_related('produto').values(
            'produto_id', 'produto__nome'
        ).annotate(
            total_vendido=Sum(F('quantidade') * F('preco_venda')),
            custo_total=Sum(F('quantidade') * F('produto__preco_custo')),
        ).annotate(
            margem_bruta=F('total_vendido') - F('custo_total'),
            percentual_margem_bruta=F('margem_bruta') * 100 / F('total_vendido', output_field=DecimalField())
        ).order_by('-margem_bruta')

        # 4. Serialização e Formato de Resposta
        serializer = RentabilidadeItemSerializer(resultados, many=True)
        response_data = {
            "relatorio_de_rentabilidade": serializer.data,
            "filtros_aplicados": request.query_params,
            "origem_dados": "Base de Dados (Cache Miss)" # Tag de debug para provar o caching
        }
        
        # 5. GRAVAR DADOS NO CACHE
        # O método `set` envia os dados serializados para o Redis com o TTL
        bi_cache.set(cache_key, response_data, timeout=self.CACHE_TTL)
        
        return Response(response_data)

