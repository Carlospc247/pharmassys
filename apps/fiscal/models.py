# apps/fiscais/models.py
from django.db import models
from decimal import Decimal
from apps.core.models import Empresa, TimeStampedModel

class TaxaIVAAGT(TimeStampedModel):
    """
    Tabela Mestra de Impostos (Tax Table) conforme Requisitos AGT/SAF-T AO.
    Define as taxas e códigos legais para o IVA, Isenções (IS) e Não Sujeição (NS).
    """
    TAX_TYPE_CHOICES = [
        ('IVA', 'Imposto sobre o Valor Acrescentado (IVA)'),
        ('IS', 'Isenção'),
        ('NS', 'Não Sujeição'),
    ]
    
    TAX_CODE_CHOICES = [
        ('NOR', 'Normal'),
        ('INT', 'Intercalar'),
        ('RED', 'Reduzida'),
        ('ISE', 'Isento'), # Este é o mais comum para isenções
        ('NSU', 'Não Sujeito'), # Este é o mais comum para não sujeição
        # Adicionar mais códigos SAF-T se necessário
    ]
    
    TAX_EXEMPTION_REASON_CHOICES = [
        ('M99', 'Outras isenções (Art. 18.º CIVA)'),
        ('M01', 'Art. 13.º - Isenções nas Transmissões de Bens'),
        ('M02', 'Art. 14.º - Isenções nas Prestações de Serviços'),
        # Adicionar códigos específicos de Angola (ex: Isenções de Produtos Farmacêuticos)
    ]

    # Vínculo com a empresa para personalização, embora as taxas sejam tipicamente globais.
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='taxas_iva'
    )
    
    # Detalhes Fiscais
    nome = models.CharField(max_length=100, help_text="Ex: IVA Taxa Normal 14%")
    codigo_pais = models.CharField(max_length=2, default='AO', editable=False) # Angola
    tax_type = models.CharField(max_length=3, choices=TAX_TYPE_CHOICES, verbose_name="Tipo de Imposto (TaxType)")
    tax_code = models.CharField(max_length=3, choices=TAX_CODE_CHOICES, verbose_name="Código da Taxa (TaxCode)")
    
    # Taxa (apenas aplicável se tax_type for 'IVA')
    tax_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Taxa em percentagem (e.g., 14.00)"
    )
    
    # Razão de Isenção (apenas aplicável se tax_type for 'IS' ou 'NS')
    exemption_reason = models.CharField(
        max_length=3, 
        choices=TAX_EXEMPTION_REASON_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Razão de Isenção (TaxExemptionCode)"
    )
    
    # Informação Legal
    legislacao_referencia = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Taxa de IVA (AGT)"
        verbose_name_plural = "Tabela de Impostos (AGT)"
        ordering = ['-tax_percentage', 'tax_type']
        
    def __str__(self):
        if self.tax_type == 'IVA':
            return f"{self.nome} ({self.tax_percentage}%)"
        return f"{self.nome} ({self.tax_type} - {self.exemption_reason})"


class AssinaturaDigital(TimeStampedModel):
    """
    Armazena a chave pública/privada (RSA) ou apenas a chave de hash,
    utilizada para assinar documentos e garantir a cadeia de integridade.
    """
    empresa = models.OneToOneField(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='assinatura_fiscal'
    )
    
    # O hash do último documento emitido na série de documentos da empresa. 
    # CRÍTICO para a Geração do ATCUD e Cadeia de Integridade.
    ultimo_hash = models.CharField(
        max_length=256, 
        blank=True, 
        null=True, 
        verbose_name="Último Hash em Cadeia (SAF-T)"
    )
    
    chave_privada = models.TextField(
        blank=True, 
        null=True, 
        help_text="Chave privada RSA para assinatura. Mantenha em segredo!"
    )
    chave_publica = models.TextField(
        blank=True, 
        null=True, 
        help_text="Chave pública RSA."
    )
    
    dados_series_fiscais = models.JSONField(
        default=dict,
        verbose_name="Dados de Hash e Código AGT por Série"
    )
    
    data_geracao = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Assinatura Fiscal de {self.empresa.nome}"


# apps/fiscais/models.py

# ... (Seus modelos existentes, ex: TaxaIVAAGT)

from apps.core.models import TimeStampedModel, Empresa
from apps.financeiro.models import ContaPagar # Para rastrear o pagamento que gerou a retenção
from apps.fornecedores.models import Fornecedor
from apps.core.choices import TIPO_RETENCAO_CHOICES # 🚨 Adicione este CHOICES no seu core

from decimal import Decimal

# CHOICES Sugeridos para o Core:
# TIPO_RETENCAO_CHOICES = [
#     ('IRTR', 'Imposto sobre o Rendimento do Trabalho - Rendimentos Não Permanentes'),
#     ('IRPC', 'Imposto sobre o Rendimento do Património e Capitais'),
#     ('ISR', 'Imposto sobre o Rendimento - Serviços/Aquisição de Bens'), 
#     ('SISA', 'Imposto sobre o Selo'),
#     # ... Adicionar outros tipos de retenção conforme a lei Angolana (IRPC, IRT, etc.)
# ]

class RetencaoFonte(TimeStampedModel):
    """
    Registo das Retenções na Fonte efetuadas pela empresa (pagador).
    Essencial para o bloco <WithholdingTax> do SAF-T.
    """
    # Identificação
    referencia_documento = models.CharField(max_length=50, help_text="Ex: Número da Fatura do Fornecedor ou Recibo")
    data_retencao = models.DateField(help_text="Data em que a retenção foi efetuada (geralmente data de pagamento)")
    
    # Valores
    valor_base = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base tributável da retenção")
    taxa_retencao = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[Decimal('0.00'), Decimal('100.00')],
        help_text="Percentagem da taxa de retenção aplicada (ex: 6.5, 10.0)"
    )
    valor_retido = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor efetivamente retido")
    
    # Classificação Fiscal
    tipo_retencao = models.CharField(
        max_length=10, 
        choices=TIPO_RETENCAO_CHOICES, 
        help_text="Tipo de imposto retido (código SAF-T obrigatório - ex: IRPC, IRT)"
    )
    codigo_tributario = models.CharField(max_length=50, blank=True, help_text="Código da Secção/Artigo da lei fiscal (se aplicável)")
    
    # Rastreamento Contábil
    conta_pagar = models.ForeignKey(
        ContaPagar, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Conta a pagar que gerou esta retenção"
    )
    fornecedor = models.ForeignKey(
        Fornecedor, 
        on_delete=models.PROTECT, 
        help_text="Fornecedor/Prestador de serviço a quem foi efetuada a retenção"
    )
    
    # Controle
    paga_ao_estado = models.BooleanField(default=False, help_text="Indica se o valor retido já foi pago ao Estado")
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Retenção na Fonte"
        verbose_name_plural = "Retenções na Fonte"
        ordering = ['-data_retencao']

    def save(self, *args, **kwargs):
        # 🚨 Lógica de Negócio Obrigatória: Cálculo do valor retido
        if self.valor_base and self.taxa_retencao:
            self.valor_retido = self.valor_base * (self.taxa_retencao / Decimal('100.00'))
        
        # 🚨 Hook Contábil: Deve ser gerado um LançamentoFinanceiro aqui (ex: Débito em Passivo (Impostos a Pagar), Crédito em ContaPagar)
        self.gerar_lancamento_contabil() 
        
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Retenção {self.tipo_retencao} de {self.valor_retido} em {self.data_retencao}"

