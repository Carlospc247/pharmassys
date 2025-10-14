from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.vendas.models import Venda
from apps.clientes.models import Ponto

@receiver(post_save, sender=Venda)
def gerar_pontos(sender, instance, created, **kwargs):
    if created and instance.cliente:  # 🔹 só cria ponto se houver cliente
        # 1 ponto = 1 Kz gasto
        Ponto.objects.create(
            cliente=instance.cliente,
            valor=instance.total,
        )
