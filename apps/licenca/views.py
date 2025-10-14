# apps/licenca/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from .models import Licenca, PlanoLicenca, HistoricoLicenca
from apps.core.models import Empresa

@staff_member_required
def gerar_licenca(request):
    """Gerar nova licença para empresa"""
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        plano_id = request.POST.get('plano_id')
        meses = int(request.POST.get('meses', 1))
        
        empresa = get_object_or_404(Empresa, id=empresa_id)
        plano = get_object_or_404(PlanoLicenca, id=plano_id)
        
        # Verificar se já tem licença
        if hasattr(empresa, 'licenca'):
            messages.error(request, 'Empresa já possui licença!')
            return redirect('admin:licenciamento_licenca_changelist')
        
        # Criar licença
        data_vencimento = timezone.now().date() + timedelta(days=30 * meses)
        
        licenca = Licenca.objects.create(
            empresa=empresa,
            plano=plano,
            data_vencimento=data_vencimento
        )
        
        # Registrar histórico
        HistoricoLicenca.objects.create(
            licenca=licenca,
            acao='criada',
            data_nova=data_vencimento,
            observacoes=f'Licença criada para {meses} mês(es)'
        )
        
        messages.success(request, f'Licença gerada para {empresa.nome}!')
        return redirect('admin:licenciamento_licenca_change', licenca.id)
    
    # GET - mostrar formulário
    empresas_sem_licenca = Empresa.objects.filter(licenca__isnull=True)
    planos = PlanoLicenca.objects.filter(ativo=True)
    
    return render(request, 'admin/gerar_licenca.html', {
        'empresas': empresas_sem_licenca,
        'planos': planos
    })

@staff_member_required
def renovar_licenca(request, licenca_id):
    """Renovar licença existente"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    
    if request.method == 'POST':
        meses = int(request.POST.get('meses', 1))
        
        data_anterior = licenca.data_vencimento
        licenca.renovar(meses=meses)
        
        # Registrar histórico
        HistoricoLicenca.objects.create(
            licenca=licenca,
            acao='renovada',
            data_anterior=data_anterior,
            data_nova=licenca.data_vencimento,
            observacoes=f'Renovada por {meses} mês(es)'
        )
        
        messages.success(request, f'Licença renovada até {licenca.data_vencimento}!')
        return redirect('admin:licenciamento_licenca_change', licenca.id)
    
    return render(request, 'admin/renovar_licenca.html', {'licenca': licenca})

def verificar_licenca_api(request):
    """API para verificar se licença está válida"""
    if not hasattr(request.user, 'perfilusuario'):
        return JsonResponse({'valida': False, 'motivo': 'Usuário sem perfil'})
    
    empresa = request.user.perfilusuario.empresa
    
    if not hasattr(empresa, 'licenca'):
        return JsonResponse({'valida': False, 'motivo': 'Empresa sem licença'})
    
    licenca = empresa.licenca
    
    if licenca.esta_vencida:
        return JsonResponse({'valida': False, 'motivo': 'Licença vencida'})
    
    if licenca.status != 'ativa':
        return JsonResponse({'valida': False, 'motivo': 'Licença inativa'})
    
    return JsonResponse({
        'valida': True,
        'dias_restantes': licenca.dias_para_vencer,
        'plano': licenca.plano.nome
    })

