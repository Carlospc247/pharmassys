# apps/produtos/tasks.py
from apps.produtos.models import Lote, AlertaProdutoExpiracao
from django.utils import timezone

def gerar_alertas_produtos():
    hoje = timezone.now().date()
    lotes = Lote.objects.filter(data_validade__gte=hoje)
    for lote in lotes:
        dias_para_vencer = (lote.data_validade - hoje).days
        if dias_para_vencer <= 30:
            alerta, created = AlertaProdutoExpiracao.objects.get_or_create(
                lote=lote,
                empresa=lote.produto.empresa,
                defaults={'dias_alerta': 30}
            )

