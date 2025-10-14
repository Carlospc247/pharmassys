# apps/core/context_processors.py
from django.utils import timezone
from datetime import timedelta
from apps.vendas.models import Venda
from apps.produtos.models import Lote

def dashboard_data(request):
    """Context processor para dados globais do dashboard"""
    if not request.user.is_authenticated or not hasattr(request.user, 'empresa'):
        return {}
    
    empresa = request.user.empresa
    if not empresa:
        return {}
    
    hoje = timezone.now().date()
    
    # Notificações rápidas
    notificacoes = []
    
    # Produtos vencendo hoje
    vencendo_hoje = Lote.objects.filter(
        produto__ativo=True,
        data_validade=hoje,
        quantidade_atual__gt=0
    ).count()
    
    if vencendo_hoje > 0:
        notificacoes.append({
            'tipo': 'warning',
            'mensagem': f'{vencendo_hoje} produto(s) vencem hoje!',
            'url': '/produtos/vencimentos/'
        })
    
    # Vendas sem pagamento há mais de 1 hora
    uma_hora_atras = timezone.now() - timedelta(hours=1)
    vendas_pendentes = Venda.objects.filter(
        empresa=empresa,
        status='aguardando_pagamento',
        created_at__lt=uma_hora_atras
    ).count()
    
    if vendas_pendentes > 0:
        notificacoes.append({
            'tipo': 'info',
            'mensagem': f'{vendas_pendentes} venda(s) aguardando pagamento',
            'url': '/vendas/pendentes/'
        })
    
    return {
        'notificacoes_globais': notificacoes,
        'count_notificacoes': len(notificacoes)
    }


