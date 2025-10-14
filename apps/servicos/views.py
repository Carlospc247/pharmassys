# Em apps/servicos/views.py

from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from apps.clientes.models import Cliente
from .models import Servico, AgendamentoServico
from .forms import ServicoForm, AgendamentoServicoForm



# --- VIEW BASE (BOA PRÁTICA) ---
class ServicoPermissionMixin(LoginRequiredMixin):
    def get_queryset(self):
        empresa = self.request.user.funcionario.empresa
        return self.model.objects.filter(empresa=empresa)
    
    def get_empresa(self):
        return self.request.user.funcionario.empresa

# --- CRUD DO CATÁLOGO DE SERVIÇOS ---
class ServicoListView(ServicoPermissionMixin, ListView):
    model = Servico
    template_name = 'servicos/servico_list.html'
    context_object_name = 'servicos'

class ServicoCreateView(ServicoPermissionMixin, CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'servicos/servico_form.html'
    success_url = reverse_lazy('servicos:servico_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs
    
    def form_valid(self, form):
        servico = form.save(commit=False)
        servico.empresa = self.get_empresa()
        servico.usuario_criacao = self.request.user
        # Valores placeholder para campos obrigatórios que não estão no form
        servico.cliente = Cliente.objects.filter(empresa=self.get_empresa()).first() 
        servico.data_agendamento = timezone.now()
        servico.save()
        messages.success(self.request, "Serviço de catálogo criado com sucesso.")
        return redirect(self.success_url)

class ServicoUpdateView(ServicoPermissionMixin, UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = 'servicos/servico_form.html'
    success_url = reverse_lazy('servicos:servico_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Serviço de catálogo atualizado com sucesso.")
        return super().form_valid(form)

class ServicoDeleteView(ServicoPermissionMixin, DeleteView):
    model = Servico
    template_name = 'servicos/servico_confirm_delete.html'
    success_url = reverse_lazy('servicos:servico_list')

    def form_valid(self, form):
        messages.success(self.request, f"Serviço '{self.object.nome}' eliminado com sucesso.")
        return super().form_valid(form)

# --- CRUD DE AGENDAMENTOS ---
class AgendamentoListView(ServicoPermissionMixin, ListView):
    model = AgendamentoServico
    template_name = 'servicos/agendamento_list.html'
    context_object_name = 'agendamentos'

class AgendamentoCreateView(ServicoPermissionMixin, CreateView):
    model = AgendamentoServico
    form_class = AgendamentoServicoForm
    template_name = 'servicos/agendamento_form.html'
    success_url = reverse_lazy('servicos:agendamento_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs

    def form_valid(self, form):
        form.instance.empresa = self.get_empresa()
        messages.success(self.request, "Agendamento criado com sucesso.")
        return super().form_valid(form)

class AgendamentoUpdateView(ServicoPermissionMixin, UpdateView):
    model = AgendamentoServico
    form_class = AgendamentoServicoForm
    template_name = 'servicos/agendamento_form.html'
    success_url = reverse_lazy('servicos:agendamento_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.get_empresa()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Agendamento atualizado com sucesso.")
        return super().form_valid(form)

class AgendamentoDeleteView(ServicoPermissionMixin, DeleteView):
    model = AgendamentoServico
    template_name = 'servicos/agendamento_confirm_delete.html'
    success_url = reverse_lazy('servicos:agendamento_list')

    def form_valid(self, form):
        messages.success(self.request, f"Agendamento para '{self.object.cliente.nome_completo}' eliminado com sucesso.")
        return super().form_valid(form)

# Adicione aqui as views IniciarServicoView e FinalizarServicoView se precisar delas
# ...

# Em apps/servicos/views.py

from django.views.generic import View, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Servico, AgendamentoServico
from .forms import FinalizarServicoForm

# ... (suas outras views CRUD) ...

# --- VIEW DE DETALHES (ONDE FICAM OS BOTÕES) ---

class AgendamentoDetailView(ServicoPermissionMixin, DetailView):
    model = AgendamentoServico
    template_name = 'servicos/agendamento_detail.html'
    context_object_name = 'agendamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Agendamento #{self.object.id}"
        # Adiciona o formulário para a ação de finalizar
        context['finalizar_form'] = FinalizarServicoForm()
        return context

# --- VIEWS DE AÇÃO ---

class IniciarServicoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        agendamento = get_object_or_404(AgendamentoServico, pk=kwargs['pk'], empresa=request.user.funcionario.empresa)
        
        # A lógica para criar/obter o Serviço e iniciar
        servico, created = Servico.objects.get_or_create(
            agendamento=agendamento,
            defaults={
                'empresa': agendamento.empresa,
                'nome': agendamento.servico.nome,
                'categoria': agendamento.servico.categoria,
                'cliente': agendamento.cliente,
                'funcionario': agendamento.funcionario,
                'data_agendamento': agendamento.data_hora,
                'duracao_minutos': agendamento.duracao_minutos,
                'preco_servico': agendamento.servico.preco_padrao,
                'usuario_criacao': request.user,
                'status': 'agendado' # Status inicial no modelo Servico
            }
        )

        try:
            servico.iniciar_servico()
            agendamento.status = 'em_andamento'
            agendamento.save()
            messages.success(request, f"Serviço '{servico.numero_servico}' iniciado com sucesso.")
        except ValidationError as e:
            messages.error(request, e.message)
            
        return redirect('servicos:agendamento_detail', pk=agendamento.pk)

class FinalizarServicoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        agendamento = get_object_or_404(AgendamentoServico, pk=kwargs['pk'], empresa=request.user.funcionario.empresa)
        servico_realizado = getattr(agendamento, 'servico', None)

        if not servico_realizado:
            messages.error(request, "Não é possível finalizar um serviço que não foi iniciado.")
            return redirect('servicos:agendamento_detail', pk=agendamento.pk)

        form = FinalizarServicoForm(request.POST)
        if form.is_valid():
            try:
                servico_realizado.finalizar_servico(
                    resultado=form.cleaned_data['resultado_servico'],
                    recomendacoes=form.cleaned_data['recomendacoes']
                )
                agendamento.status = 'finalizado'
                agendamento.save()
                messages.success(request, "Serviço finalizado com sucesso.")
            except ValidationError as e:
                messages.error(request, e.message)
        else:
            messages.error(request, "Formulário inválido. Por favor, preencha os campos necessários.")
            
        return redirect('servicos:agendamento_detail', pk=agendamento.pk)




from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET"])
def listar_servicos_api(request):
    """
    API para listar serviços no PDV
    """
    try:
        if hasattr(request.user, 'funcionario') and request.user.funcionario:
            empresa = request.user.funcionario.empresa
        else:
            return JsonResponse({
                'success': False,
                'message': 'Empresa não encontrada'
            }, status=400)
        
        servicos = Servico.objects.filter(
            empresa=empresa,
            ativo=True
        ).select_related('categoria')
        
        servicos_data = []
        for servico in servicos:
            servicos_data.append({
                'id': servico.id,
                'nome': servico.nome,
                'categoria': servico.categoria.nome if servico.categoria else '',
                'categoria_id': servico.categoria.id if servico.categoria else None,
                'preco': float(servico.preco_padrao),
                'descricao': getattr(servico, 'instrucoes_padrao', ''),
                'disponivel': True  # Serviços geralmente estão sempre disponíveis
            })
        
        return JsonResponse({
            'success': True,
            'servicos': servicos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)
    
    
