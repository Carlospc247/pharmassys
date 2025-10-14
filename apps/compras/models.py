from django.db import models



class Compra(models.Model):
    fornecedor = models.ForeignKey('fornecedores.Fornecedor', on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    # Exemplo de método para total da compra
    def total(self):
        return sum(item.subtotal for item in self.itens.all())


class ItemCompra(models.Model):
    compra = models.ForeignKey('Compra', on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey('produtos.Produto', on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


