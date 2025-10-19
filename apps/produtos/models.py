# apps/produtos/models.py
from django.conf import settings
from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.utils.html import format_html
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from apps.core.models import Empresa, TimeStampedModel, Categoria




class Fabricante(TimeStampedModel):
    """Fabricante de produtos"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='fabricantes')
    nome = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True, verbose_name="NIF")
    origem = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Fabricante'
        verbose_name_plural = 'Fabricantes'
        unique_together = ['empresa', 'nome']
        
    def __str__(self):
        return self.nome


from django.db import models
from decimal import Decimal

class Produto(TimeStampedModel):
    """Produto do estoque"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    fornecedor = models.ForeignKey('fornecedores.Fornecedor', on_delete=models.SET_NULL, null=True, blank=True)
    fabricante = models.ForeignKey(Fabricante, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Identificação
    codigo_interno = models.CharField(max_length=50)
    codigo_barras = models.CharField(max_length=50, unique=True)
    nome_produto = models.CharField(max_length=200)
    nome_comercial = models.CharField(max_length=200)

    iva_percentual = models.ForeignKey(
        'fiscal.TaxaIVAAGT',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name="Taxa de IVA/Imposto Legal (AGT)"
    )
    
    desconto_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="DESCONTO (%)"
    )
    observacoes = models.TextField(blank=True, null=True)

    # Estoque
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    estoque_maximo = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    
    # Preços
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    margem_lucro = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    foto = models.ImageField(upload_to='produtos/fotos/', null=True, blank=True, default='produtos/fotos/produtos.png')
    
    # Status
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Converte a margem de lucro de percentual para decimal
        if self.margem_lucro is not None and self.preco_custo is not None:
            margem_decimal = self.margem_lucro / Decimal('100.00')
            
            # Recalcula o preço de venda e a margem de lucro
            self.preco_venda = self.preco_custo + (self.preco_custo * margem_decimal)
            self.margem_lucro = (self.preco_venda - self.preco_custo) / self.preco_custo * Decimal('100.00')

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        unique_together = ['empresa', 'codigo_interno']
        
    def __str__(self):
        return self.nome_produto
    
    @property
    def valor_estoque(self):
        if self.estoque_atual is not None and self.preco_custo is not None:
            return self.estoque_atual * self.preco_custo
        return Decimal('0.00')
    
    def preco_venda_display(self):
        return f"AKZ {self.preco_venda}"
    preco_venda_display.short_description = 'Preço de Venda'

    @property
    def iva_percentual_display(self):
        """Compatibilidade retroativa — devolve o valor da iva_percentual"""
        if self.iva_percentual:
            return self.iva_percentual.tax_percentage
        return Decimal('0.00')
    
    @property
    def tipo_produto(self):
        """Define o ProductType do SAF-T. Assumimos que são Bens (M - Merchandise)."""
        # Em Angola, deve-se usar 'M' (Mercadorias) ou 'S' (Serviços)
        # O seu sistema parece focado em Mercadorias (Lotes).
        # Implemente um campo 'is_service' se necessário, mas para já:
        return 'M'


class Lote(TimeStampedModel):
    """Lote de produtos"""
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=50)
    data_validade = models.DateField()
    quantidade_inicial = models.IntegerField()
    quantidade_atual = models.IntegerField()
    preco_custo_lote = models.DecimalField(max_digits=10, decimal_places=2)
    
    def esta_vencido(self):
        return self.data_validade < timezone.now().date()

    def dias_para_vencer(self):
        return (self.data_validade - timezone.now().date()).days

    def esta_perto_do_vencimento(self, dias_alerta=30):
        return self.dias_para_vencer() <= dias_alerta

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        unique_together = ['produto', 'numero_lote']
        
    def __str__(self):
        return f"{self.produto.nome_comercial} - Lote {self.numero_lote}"


class ControleVencimento(TimeStampedModel):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name="controles_vencimento")
    dias_para_alerta = models.IntegerField(default=30)
    alerta_gerado = models.BooleanField(default=False)

    def precisa_alerta(self):
        return self.lote.esta_perto_do_vencimento(self.dias_para_alerta)



class HistoricoPreco(models.Model):
   
    produto = models.ForeignKey(
        "Produto",
        on_delete=models.CASCADE,
        related_name="historico_precos"
    )

    # Preços anteriores
    preco_custo_anterior = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    preco_venda_anterior = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])

    # Preços novos
    preco_custo_novo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    preco_venda_novo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])

    motivo = models.CharField(max_length=100)
    observacoes = models.TextField(blank=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_precos_registrados"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Preço"
        verbose_name_plural = "Históricos de Preços"
        ordering = ["-created_at"]

    def __str__(self):
        data = timezone.localtime(self.created_at).strftime("%d/%m/%Y %H:%M") if self.created_at else "—"
        return f"{self.produto} - {data}"

    @property
    def variacao_custo_percentual(self):
        if self.preco_custo_anterior and self.preco_custo_anterior != 0:
            return ((self.preco_custo_novo - self.preco_custo_anterior) / self.preco_custo_anterior) * 100
        return Decimal("0")

    @property
    def variacao_venda_percentual(self):
        if self.preco_venda_anterior and self.preco_venda_anterior != 0:
            return ((self.preco_venda_novo - self.preco_venda_anterior) / self.preco_venda_anterior) * 100
        return Decimal("0")
    


  