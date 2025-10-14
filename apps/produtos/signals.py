# apps/produtos/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import Lote, Produto 

@receiver(post_save, sender=Lote)
@receiver(post_delete, sender=Lote)
def atualizar_estoque_produto(sender, instance, **kwargs):
    # Garante que o produto existe antes de tentar atualizá-lo.
    if instance.produto:
        produto = instance.produto
        
        # Recalcula o estoque total somando a quantidade_atual de todos os lotes
        # associados a este produto.
        estoque_total = Lote.objects.filter(produto=produto).aggregate(total=Sum('quantidade_atual'))['total'] or 0
        
        # Evita a recursão infinita salvando apenas se o valor realmente mudou.
        if produto.estoque_atual != estoque_total:
            produto.estoque_atual = estoque_total
            produto.save(update_fields=['estoque_atual'])


