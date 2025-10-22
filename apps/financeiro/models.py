# apps/financeiro/models.py
from decimal import Decimal
from datetime import date, datetime, timedelta
import uuid

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import TimeStampedModel, Empresa, Usuario, Loja
from apps.fornecedores.models import Fornecedor
from apps.clientes.models import Cliente
from apps.vendas.models import Venda

from pharmassys import settings




class PlanoContas(TimeStampedModel):
    """Plano de contas contábil"""
    TIPO_CONTA_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('ativo', 'Ativo'),
        ('passivo', 'Passivo'),
        ('patrimonio', 'Patrimônio Líquido'),
    ]
    
    NATUREZA_CHOICES = [
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]
    
    # Identificação
    codigo = models.CharField(max_length=20, unique=True, help_text="Código da conta")
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    # Hierarquia
    conta_pai = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='contas_filhas'
    )
    nivel = models.IntegerField(default=1, help_text="Nível hierárquico da conta")
    
    # Características
    tipo_conta = models.CharField(max_length=15, choices=TIPO_CONTA_CHOICES)
    natureza = models.CharField(max_length=10, choices=NATUREZA_CHOICES)
    aceita_lancamento = models.BooleanField(default=True, help_text="Permite lançamentos diretos")
    
    # Configurações
    ativa = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Plano de Contas"
        verbose_name_plural = "Planos de Contas"
        unique_together = [['codigo', 'empresa']]
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def codigo_completo(self):
        """Código completo com hierarquia"""
        if self.conta_pai:
            return f"{self.conta_pai.codigo_completo}.{self.codigo}"
        return self.codigo
    
    @property
    def nome_completo(self):
        """Nome completo com hierarquia"""
        if self.conta_pai:
            return f"{self.conta_pai.nome_completo} > {self.nome}"
        return self.nome


class CentroCusto(TimeStampedModel):
    """Centros de custo para controle gerencial"""
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    # Responsável
    responsavel = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Configurações
    ativo = models.BooleanField(default=True)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, null=True, blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"
        unique_together = [['codigo', 'empresa']]
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ContaBancaria(TimeStampedModel):
    """Contas bancárias da empresa"""
    TIPO_CONTA_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Poupança'),
        ('investimento', 'Conta Investimento'),
        ('cartao', 'Cartão de Crédito'),
        ('caixa', 'Caixa'),
    ]
    
    # Identificação
    nome = models.CharField(max_length=200)
    banco = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20)
    conta = models.CharField(max_length=30)
    digito = models.CharField(max_length=5, blank=True)
    tipo_conta = models.CharField(max_length=15, choices=TIPO_CONTA_CHOICES, default='corrente')
    
    # Saldos
    saldo_inicial = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Saldo inicial da conta"
    )
    saldo_atual = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Saldo atual calculado"
    )
    
    # Limites
    limite_credito = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Limite de crédito/cheque especial"
    )
    plano_contas_ativo = models.ForeignKey(
        PlanoContas,
        on_delete=models.PROTECT,
        related_name='contas_bancarias_ativo',
        help_text="Conta do Plano de Contas (Ativo) associada a este Caixa/Banco."
    )
        
    # Configurações
    ativa = models.BooleanField(default=True)
    conta_principal = models.BooleanField(default=False)
    permite_saldo_negativo = models.BooleanField(default=False)
    
    # Integração
    codigo_integracao = models.CharField(max_length=50, blank=True)
    ultima_conciliacao = models.DateField(null=True, blank=True)
    
    observacoes = models.TextField(blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"
        ordering = ['-conta_principal', 'banco', 'conta']
    
    def __str__(self):
        return f"{self.banco} - Ag: {self.agencia} Cc: {self.conta}"
    
    def atualizar_saldo(self):
        """Atualiza o saldo atual da conta"""
        movimentacoes = self.movimentacoes.filter(confirmada=True)
        
        # Somar entradas e subtrair saídas
        entradas = movimentacoes.filter(tipo_movimentacao='entrada').aggregate(
            total=models.Sum('valor')
        )['total'] or Decimal('0.00')
        
        saidas = movimentacoes.filter(tipo_movimentacao='saida').aggregate(
            total=models.Sum('valor')
        )['total'] or Decimal('0.00')
        
        self.saldo_atual = self.saldo_inicial + entradas - saidas
        self.save()
        
        return self.saldo_atual
    
    @property
    def saldo_disponivel(self):
        """Saldo disponível (incluindo limite)"""
        return self.saldo_atual + self.limite_credito


class MovimentacaoFinanceira(TimeStampedModel):
    """Movimentações financeiras"""
    TIPO_MOVIMENTACAO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('transferencia', 'Transferência'),
    ]
    
    TIPO_DOCUMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cheque', 'Cheque'),
        ('transferencia', 'Transferência'),
        ('cartao', 'Cartão'),
        ('debito_automatico', 'Débito Automático'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('estornada', 'Estornada'),
    ]
    
    # Identificação
    numero_documento = models.CharField(max_length=50, blank=True)
    tipo_movimentacao = models.CharField(max_length=15, choices=TIPO_MOVIMENTACAO_CHOICES)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    
    # Datas
    data_movimentacao = models.DateField()
    data_vencimento = models.DateField(null=True, blank=True)
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    
    # Valores
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recibo = models.ForeignKey(
        'vendas.Recibo', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='movimentacoes_financeiras_origem',
        help_text="Recibo de Pagamento (REC) que originou esta entrada."
    )
    # Contas
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name='movimentacoes')
    conta_destino = models.ForeignKey(
        ContaBancaria, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='transferencias_recebidas',
        help_text="Para transferências entre contas"
    )
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.PROTECT)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    
    # Relacionamentos
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    venda_relacionada = models.ForeignKey(Venda, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Descrição
    descricao = models.CharField(max_length=255)
    observacoes = models.TextField(blank=True)
    
    # Controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    confirmada = models.BooleanField(default=False)
    conciliada = models.BooleanField(default=False)
    data_conciliacao = models.DateField(null=True, blank=True)
    
    # Responsável
    usuario_responsavel = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    
    # Dados do cheque (se aplicável)
    numero_cheque = models.CharField(max_length=20, blank=True)
    banco_cheque = models.CharField(max_length=100, blank=True)
    emissor_cheque = models.CharField(max_length=200, blank=True)
    

    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    
    
    class Meta:
        verbose_name = "Movimentação Financeira"
        verbose_name_plural = "Movimentações Financeiras"
        indexes = [
            models.Index(fields=['data_movimentacao', 'empresa']),
            models.Index(fields=['conta_bancaria', 'confirmada']),
            models.Index(fields=['status', 'data_vencimento']),
            models.Index(fields=['tipo_movimentacao', 'data_movimentacao']),
        ]
        ordering = ['-data_movimentacao', '-created_at']
    
    def __str__(self):
        sinal = '+' if self.tipo_movimentacao == 'entrada' else '-'
        return f"{sinal}R$ {self.valor} - {self.descricao}"
    
    def save(self, *args, **kwargs):
        # Calcular valor total
        self.total = self.valor + self.valor_juros + self.valor_multa - self.valor_desconto
        
        super().save(*args, **kwargs)
        
        # Atualizar saldo da conta se confirmada
        if self.confirmada:
            self.conta_bancaria.atualizar_saldo()
            if self.conta_destino:
                self.conta_destino.atualizar_saldo()
    
    def confirmar_movimentacao(self, usuario):
        """Confirma a movimentação"""
        if self.confirmada:
            raise ValidationError("Movimentação já confirmada")
        
        self.confirmada = True
        self.status = 'confirmada'
        self.data_confirmacao = datetime.now()
        self.save()
        
        # Criar transferência de destino se for transferência
        if self.tipo_movimentacao == 'transferencia' and self.conta_destino:
            MovimentacaoFinanceira.objects.create(
                tipo_movimentacao='entrada',
                tipo_documento=self.tipo_documento,
                data_movimentacao=self.data_movimentacao,
                valor=self.valor,
                conta_bancaria=self.conta_destino,
                plano_contas=self.plano_contas,
                centro_custo=self.centro_custo,
                descricao=f"Transferência de {self.conta_bancaria}",
                status='confirmada',
                confirmada=True,
                data_confirmacao=datetime.now(),
                usuario_responsavel=usuario,
                empresa=self.empresa
            )
    
    def estornar_movimentacao(self, usuario, motivo=""):
        """Estorna a movimentação"""
        if not self.confirmada:
            raise ValidationError("Apenas movimentações confirmadas podem ser estornadas")
        
        self.status = 'estornada'
        self.observacoes += f"\nEstornada em {datetime.now()}: {motivo}"
        self.save()
        
        # Criar movimentação de estorno
        MovimentacaoFinanceira.objects.create(
            tipo_movimentacao='saida' if self.tipo_movimentacao == 'entrada' else 'entrada',
            tipo_documento='estorno',
            data_movimentacao=date.today(),
            valor=self.valor,
            conta_bancaria=self.conta_bancaria,
            plano_contas=self.plano_contas,
            centro_custo=self.centro_custo,
            descricao=f"Estorno: {self.descricao}",
            observacoes=f"Estorno da movimentação {self.id}: {motivo}",
            status='confirmada',
            confirmada=True,
            data_confirmacao=datetime.now(),
            usuario_responsavel=usuario,
            empresa=self.empresa
        )


class ContaPai(models.Model):
    """Conta principal que consolida parcelas"""
    
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('vencida', 'Vencida'),
        ('paga', 'Paga'),
        ('recebida', 'Recebida'),
        ('cancelada', 'Cancelada'),
        ('renegociada', 'Renegociada'),
    ]

    # Identificação
    numero_documento = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    
    # Datas
    data_emissao = models.DateField()
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    data_recebimento = models.DateField(null=True, blank=True)

    # Valores
    valor_original = models.DecimalField(max_digits=12, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_recebido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='aberta')
    observacoes = models.TextField(blank=True)

    # Relacionamentos opcionais para integração com contas a pagar ou receber
    empresa = models.ForeignKey('core.Empresa', on_delete=models.CASCADE)
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    fornecedor = models.ForeignKey('fornecedores.Fornecedor', on_delete=models.SET_NULL, null=True, blank=True)
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.PROTECT, null=True, blank=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        verbose_name = "Conta Principal"
        verbose_name_plural = "Contas Principais"
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['status', 'empresa']),
        ]
        ordering = ['data_vencimento']

    def __str__(self):
        return f"{self.numero_documento} - {self.descricao} - R$ {self.valor_original}"

    def atualizar_saldo_status(self):
        """Atualiza saldo e status baseado nas parcelas"""
        # Para pagamento
        total_pago = self.parcelas.aggregate(total=models.Sum('valor_pago'))['total'] or 0
        self.valor_pago = total_pago

        # Para recebimento
        total_recebido = self.parcelas.aggregate(total=models.Sum('valor_recebido'))['total'] or 0
        self.valor_recebido = total_recebido

        # Calcula saldo
        self.valor_saldo = (self.valor_original + self.valor_juros + self.valor_multa - self.valor_desconto) - max(total_pago, total_recebido)

        # Atualiza status
        hoje = date.today()
        if self.valor_saldo <= 0:
            if self.valor_pago > 0:
                self.status = 'paga'
                if not self.data_pagamento:
                    self.data_pagamento = hoje
            elif self.valor_recebido > 0:
                self.status = 'recebida'
                if not self.data_recebimento:
                    self.data_recebimento = hoje
        elif self.data_vencimento < hoje:
            self.status = 'vencida'
        else:
            self.status = 'aberta'

        self.save()

    @property
    def dias_vencimento(self):
        """Dias para vencimento (negativo se vencida)"""
        if not self.data_vencimento:
            return None  # ou 0, conforme sua regra de negócio
        return (self.data_vencimento - date.today()).days


    @property
    def esta_vencida(self):
        """Verifica se a conta está vencida"""
        if not self.data_vencimento:
            return False
        return self.data_vencimento < date.today() and self.status in ['aberta', 'vencida']



class ContaPagar(TimeStampedModel):
    """Contas a pagar"""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('vencida', 'Vencida'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
        ('renegociada', 'Renegociada'),
    ]
    
    TIPO_CONTA_CHOICES = [
        ('fornecedor', 'Fornecedor'),
        ('funcionario', 'Funcionário'),
        ('servico', 'Serviço'),
        ('imposto', 'Imposto'),
        ('emprestimo', 'Empréstimo'),
        ('financiamento', 'Financiamento'),
        ('cartao', 'Cartão de Crédito'),
        ('outros', 'Outros'),
    ]
    
    # Identificação
    numero_documento = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    tipo_conta = models.CharField(max_length=15, choices=TIPO_CONTA_CHOICES)
    
    # Datas
    data_emissao = models.DateField()
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    # Valores
    valor_original = models.DecimalField(max_digits=12, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Relacionamentos
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.PROTECT)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    
    # Parcelamento
    numero_parcela = models.IntegerField(default=1)
    total_parcelas = models.IntegerField(default=1)
    conta_pai = models.ForeignKey(
        ContaPai, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='parcelas_pagar'
    )
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='aberta')
    observacoes = models.TextField(blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['fornecedor', 'status']),
            models.Index(fields=['status', 'empresa']),
        ]
        ordering = ['data_vencimento']
    
    def __str__(self):
        return f"{self.numero_documento} - {self.descricao} - R$ {self.valor_original}"
    
    
    def save(self, *args, **kwargs):
        # Calcular valor do saldo
        total = self.valor_original + self.valor_juros + self.valor_multa - self.valor_desconto
        self.valor_saldo = total - self.valor_pago
        
        # Atualizar status baseado no pagamento
        if self.valor_saldo <= 0 and self.valor_pago > 0:
            self.status = 'paga'
            if not self.data_pagamento:
                self.data_pagamento = date.today()
        elif self.data_vencimento < date.today() and self.status == 'aberta':
            self.status = 'vencida'
        
        super().save(*args, **kwargs)

        # Atualiza a conta pai se existir
        if self.conta_pai:
            self.conta_pai.atualizar_saldo_status()

    @property
    def dias_vencimento(self):
        """Dias para vencimento (negativo se vencida)"""
        if not self.data_vencimento:
            return None  # ou 0, conforme sua regra de negócio
        return (self.data_vencimento - date.today()).days


    @property
    def esta_vencida(self):
        """Verifica se a conta está vencida"""
        if not self.data_vencimento:
            return False
        return self.data_vencimento < date.today() and self.status in ['aberta', 'vencida']
    
    def pagar(self, valor_pagamento, conta_bancaria, tipo_documento='transferencia', observacoes=""):
        if self.status not in ['aberta', 'vencida']:
            raise ValidationError("Apenas contas abertas ou vencidas podem ser pagas")
        if valor_pagamento <= 0:
            raise ValidationError("Valor do pagamento deve ser maior que zero")
        
        # Registrar movimentação financeira
        movimentacao = MovimentacaoFinanceira.objects.create(
            tipo_movimentacao='saida',
            tipo_documento=tipo_documento,
            data_movimentacao=date.today(),
            valor=valor_pagamento,
            conta_bancaria=conta_bancaria,
            plano_contas=self.plano_contas,
            centro_custo=self.centro_custo,
            fornecedor=self.fornecedor,
            descricao=f"Pagamento: {self.descricao}",
            observacoes=f"Conta a pagar: {self.numero_documento}. {observacoes}",
            status='confirmada',
            confirmada=True,
            data_confirmacao=datetime.now(),
            usuario_responsavel=conta_bancaria.empresa.funcionarios.first().usuario,
            empresa=self.empresa
        )
        
        # Atualizar valores da parcela
        self.valor_pago += valor_pagamento
        self.save()

        # Atualizar saldo da conta pai, se existir
        if self.conta_pai:
            total_pago = self.conta_pai.parcelas.aggregate(total=models.Sum('valor_pago'))['total'] or 0
            self.conta_pai.valor_pago = total_pago
            self.conta_pai.valor_saldo = self.conta_pai.valor_original + self.conta_pai.valor_juros + self.conta_pai.valor_multa - self.conta_pai.valor_desconto - total_pago
            if self.conta_pai.valor_saldo <= 0:
                self.conta_pai.status = 'paga'
                if not self.conta_pai.data_pagamento:
                    self.conta_pai.data_pagamento = date.today()
            self.conta_pai.save()

        return movimentacao


class ContaReceberManager(models.Manager):
    def abertas(self):
        return self.filter(status='aberta')

    def vencidas(self):
        return self.filter(status='vencida')

    def vencendo(self):
        hoje = date.today()
        return self.filter(
            status='aberta',
            data_vencimento__lte=hoje + timedelta(days=3),
            data_vencimento__gte=hoje
        )

    def recebidas(self):
        return self.filter(status='recebida')


class ContaReceber(TimeStampedModel):
    """Contas a receber"""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('vencida', 'Vencida'),
        ('recebida', 'Recebida'),
        ('cancelada', 'Cancelada'),
        ('renegociada', 'Renegociada'),
    ]
    
    TIPO_CONTA_CHOICES = [
        ('venda', 'Venda'),
        ('servico', 'Serviço'),
        ('aluguel', 'Aluguel'),
        ('juros', 'Juros'),
        ('outros', 'Outros'),
    ]
    
    # Identificação
    numero_documento = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    tipo_conta = models.CharField(max_length=15, choices=TIPO_CONTA_CHOICES, default='venda')
    
    # Datas
    data_emissao = models.DateField()
    data_vencimento = models.DateField()
    data_recebimento = models.DateField(null=True, blank=True)
    
    # Valores
    valor_original = models.DecimalField(max_digits=12, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_recebido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Relacionamentos
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    venda = models.ForeignKey('vendas.Venda', on_delete=models.SET_NULL, null=True, blank=True)
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.PROTECT)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    
    # Parcelamento
    numero_parcela = models.IntegerField(default=1)
    total_parcelas = models.IntegerField(default=1)
    conta_pai = models.ForeignKey(
        ContaPai, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='parcelas_receber'
    )
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='aberta')
    observacoes = models.TextField(blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    objects = ContaReceberManager()
    
    class Meta:
        verbose_name = "Conta a Receber"
        verbose_name_plural = "Contas a Receber"
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['status', 'empresa']),
        ]
        ordering = ['data_vencimento']
    
    def __str__(self):
        return f"{self.numero_documento} - {self.descricao} - R$ {self.valor_original}"
    

    def save(self, *args, **kwargs):
        total = self.valor_original + self.valor_juros + self.valor_multa - self.valor_desconto
        self.valor_saldo = total - self.valor_recebido

        hoje = date.today()

        if self.valor_saldo <= 0 and self.valor_recebido > 0:
            self.status = 'recebida'
            if not self.data_recebimento:
                self.data_recebimento = hoje
        elif self.data_vencimento < hoje and self.status != 'recebida':
            self.status = 'vencida'
        elif (self.data_vencimento - hoje).days <= 3 and self.status == 'aberta':
            pass
        else:
            self.status = 'aberta'

        super().save(*args, **kwargs)

        # Atualiza a conta pai se existir
        if self.conta_pai:
            self.conta_pai.atualizar_saldo_status()

    @property
    def dias_vencimento(self):
        """Dias para vencimento (negativo se vencida)"""
        if not self.data_vencimento:
            return None  # ou 0, conforme sua regra de negócio
        return (self.data_vencimento - date.today()).days


    @property
    def esta_vencida(self):
        """Verifica se a conta está vencida"""
        if not self.data_vencimento:
            return False
        return self.data_vencimento < date.today() and self.status in ['aberta', 'vencida']
    
    def receber(self, valor_recebimento, conta_bancaria, tipo_documento='transferencia', observacoes=""):
        if self.status not in ['aberta', 'vencida']:
            raise ValidationError("Apenas contas abertas ou vencidas podem ser recebidas")
        if valor_recebimento <= 0:
            raise ValidationError("Valor do recebimento deve ser maior que zero")
        
        # Registrar movimentação financeira
        movimentacao = MovimentacaoFinanceira.objects.create(
            tipo_movimentacao='entrada',
            tipo_documento=tipo_documento,
            data_movimentacao=date.today(),
            valor=valor_recebimento,
            conta_bancaria=conta_bancaria,
            plano_contas=self.plano_contas,
            centro_custo=self.centro_custo,
            cliente=self.cliente,
            venda_relacionada=self.venda,
            descricao=f"Recebimento: {self.descricao}",
            observacoes=f"Conta a receber: {self.numero_documento}. {observacoes}",
            status='confirmada',
            confirmada=True,
            data_confirmacao=timezone.now(),
            usuario_responsavel=conta_bancaria.empresa.funcionarios.first().usuario,
            empresa=self.empresa
        )
        
        # Atualizar valores da parcela
        self.valor_recebido += valor_recebimento
        self.save()

        # Atualizar saldo da conta pai, se existir
        if self.conta_pai:
            total_recebido = self.conta_pai.parcelas.aggregate(total=models.Sum('valor_recebido'))['total'] or 0
            self.conta_pai.valor_recebido = total_recebido
            self.conta_pai.valor_saldo = self.conta_pai.valor_original + self.conta_pai.valor_juros + self.conta_pai.valor_multa - self.conta_pai.valor_desconto - total_recebido
            if self.conta_pai.valor_saldo <= 0:
                self.conta_pai.status = 'recebida'
                if not self.conta_pai.data_recebimento:
                    self.conta_pai.data_recebimento = date.today()
            self.conta_pai.save()

        return movimentacao

    
class FluxoCaixa(TimeStampedModel):
    """Projeção de fluxo de caixa"""
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]
    
    # Data e tipo
    data_referencia = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    # Valores
    valor_previsto = models.DecimalField(max_digits=12, decimal_places=2)
    valor_realizado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Classificação
    categoria = models.CharField(max_length=100, help_text="Categoria da movimentação")
    descricao = models.CharField(max_length=255)
    
    # Relacionamentos
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.CASCADE)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Origem da projeção
    conta_pagar = models.ForeignKey(ContaPagar, on_delete=models.SET_NULL, null=True, blank=True)
    conta_receber = models.ForeignKey(ContaReceber, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    realizado = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Fluxo de Caixa"
        verbose_name_plural = "Fluxos de Caixa"
        ordering = ['data_referencia']
    
    def __str__(self):
        sinal = '+' if self.tipo == 'entrada' else '-'
        return f"{self.data_referencia} - {sinal}R$ {self.valor_previsto} - {self.categoria}"

class ConciliacaoBancaria(TimeStampedModel):
    """Conciliação bancária"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('conciliada', 'Conciliada'),
        ('divergente', 'Divergente'),
    ]
    
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.CASCADE, related_name='conciliacoes')
    
    # Período
    data_inicio = models.DateField()
    data_fim = models.DateField()
    
    # Saldos
    saldo_banco_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_banco_final = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_sistema_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_sistema_final = models.DecimalField(max_digits=12, decimal_places=2)
    diferenca = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    data_conciliacao = models.DateTimeField(null=True, blank=True)
    responsavel = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Conciliação Bancária"
        verbose_name_plural = "Conciliações Bancárias"
        ordering = ['-data_fim']
    
    def __str__(self):
        return f"{self.conta_bancaria} - {self.data_inicio} a {self.data_fim}"
    
    def save(self, *args, **kwargs):
        # Calcular diferença
        self.diferenca = self.saldo_banco_final - self.saldo_sistema_final
        
        # Atualizar status baseado na diferença
        if abs(self.diferenca) <= Decimal('0.01'):  # Tolerância de 1 centavo
            self.status = 'conciliada'
            self.data_conciliacao = datetime.now()
        elif self.diferenca != 0:
            self.status = 'divergente'
        
        super().save(*args, **kwargs)

class OrcamentoFinanceiro(TimeStampedModel):
    """Orçamento financeiro"""
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]
    
    # Período
    ano = models.IntegerField()
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Classificação
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.CASCADE)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Valores
    valor_orcado = models.DecimalField(max_digits=12, decimal_places=2)
    valor_realizado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_variacao = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentual_realizacao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Observações
    justificativa_variacao = models.TextField(blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Orçamento Financeiro"
        verbose_name_plural = "Orçamentos Financeiros"
        unique_together = ['ano', 'mes', 'plano_contas', 'centro_custo', 'empresa']
        ordering = ['ano', 'mes']
    
    def __str__(self):
        return f"{self.ano}/{self.mes:02d} - {self.plano_contas.nome} - R$ {self.valor_orcado}"
    
    def save(self, *args, **kwargs):
        # Calcular variação e percentual
        self.valor_variacao = self.valor_realizado - self.valor_orcado
        if self.valor_orcado:
            self.percentual_realizacao = (self.valor_realizado / self.valor_orcado) * 100
        
        super().save(*args, **kwargs)
    
    def atualizar_realizado(self):
        """Atualiza valor realizado baseado nas movimentações do período"""
        from datetime import date
        
        data_inicio = date(self.ano, self.mes, 1)
        if self.mes == 12:
            data_fim = date(self.ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(self.ano, self.mes + 1, 1) - timedelta(days=1)
        
        # Buscar movimentações do período
        movimentacoes = MovimentacaoFinanceira.objects.filter(
            plano_contas=self.plano_contas,
            centro_custo=self.centro_custo,
            data_movimentacao__range=[data_inicio, data_fim],
            confirmada=True,
            empresa=self.empresa
        )
        
        if self.tipo == 'receita':
            movimentacoes = movimentacoes.filter(tipo_movimentacao='entrada')
        else:
            movimentacoes = movimentacoes.filter(tipo_movimentacao='saida')
        
        total = movimentacoes.aggregate(total=models.Sum('valor'))['total'] or Decimal('0.00')
        self.valor_realizado = total
        self.save()


class CategoriaFinanceira(models.Model):
    TIPO_DRE_CHOICES = [
        ('receita', 'Receita Bruta'),
        ('deducao', 'Deduções/Impostos'),
        ('custo', 'Custo'),
        ('despesa', 'Despesa Operacional'),
        ('financeiro', 'Resultado Financeiro'),
        ('outros', 'Outros'),
    ]

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    tipo_dre = models.CharField(max_length=20, null=False, blank=False, choices=TIPO_DRE_CHOICES, default='receita')

    def __str__(self):
        return self.nome


class LancamentoFinanceiro(TimeStampedModel): # Use TimeStampedModel para tracking
    TIPO_CHOICES = (
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    )

    # Identificação
    numero_lancamento = models.CharField(max_length=50, unique=True, help_text="ID do lançamento contábil (ex: 202509-0001)")
    data_lancamento = models.DateField(default=date.today)
    descricao = models.CharField(max_length=255)
    
    # Valores
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES) # Se é Débito ou Crédito
    valor = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]) # Deve ser sempre positivo
    
    # Contas
    plano_contas = models.ForeignKey(PlanoContas, on_delete=models.PROTECT, related_name='lancamentos')
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    
    # Rastreamento (Obrigatório para auditoria)
    origem_movimentacao = models.ForeignKey(
        MovimentacaoFinanceira, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Movimentação (Caixa/Banco) que gerou o lançamento"
    )
    # Grupo de Lançamentos (Para agrupar o débito e o crédito)
    transacao_uuid = models.UUIDField(default=uuid.uuid4, editable=False) 

    usuario_responsavel = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Lançamento Contábil"
        verbose_name_plural = "Lançamentos Contábeis"
        ordering = ['data_lancamento', 'numero_lancamento']
        # Índices para pesquisa rápida de GeneralLedgerEntries
        indexes = [
             models.Index(fields=['data_lancamento', 'plano_contas']),
             models.Index(fields=['transacao_uuid']),
        ]

    def __str__(self):
        return f"{self.numero_lancamento} | {self.data_lancamento} | {self.tipo.upper()} {self.valor}"


class MovimentoCaixa(TimeStampedModel):
    """Movimentações do caixa físico"""
    TIPO_MOVIMENTO_CHOICES = [
        ('abertura', 'Abertura do Caixa'),
        ('fechamento', 'Fechamento do Caixa'),
        ('venda', 'Venda'),
        ('recebimento', 'Recebimento'),
        ('pagamento', 'Pagamento'),
        ('sangria', 'Sangria'),
        ('suprimento', 'Suprimento'),
        ('troco', 'Troco'),
        ('devolucao', 'Devolução'),
        ('desconto', 'Desconto'),
        ('cancelamento', 'Cancelamento'),
        ('ajuste', 'Ajuste'),
        ('outros', 'Outros'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
    ('dinheiro', 'Dinheiro'),
    ('cartao_debito', 'Cartão de Débito'),
    ('cartao_credito', 'Cartão de Crédito'),
    ('transferencia', 'Transferência'),
    ('cheque', 'Cheque'),
    ('vale', 'Vale'),
    ('outros', 'Outros'),
]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('estornado', 'Estornado'),
    ]
    
    # Identificação
    numero_movimento = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Número sequencial do movimento"
    )
    
    # Data e hora
    data_movimento = models.DateField(default=date.today)
    hora_movimento = models.TimeField(auto_now_add=True)
    
    # Tipo e forma
    tipo_movimento = models.CharField(max_length=15, choices=TIPO_MOVIMENTO_CHOICES)
    forma_pagamento = models.CharField(
        "Tipo",
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='dinheiro'
    )
    
    # Valores
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Valor do movimento (positivo para entradas, negativo para saídas)"
    )
    valor_troco = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Valor do troco dado"
    )
    
    # Descrição
    descricao = models.CharField(max_length=255)
    observacoes = models.TextField(blank=True)
    
    # Relacionamentos
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        help_text="Usuário responsável pelo movimento"
    )
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    
    # Venda relacionada (se aplicável)
    venda_relacionada = models.ForeignKey(
        'vendas.Venda', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Venda que originou este movimento"
    )
    
    # Conta financeira relacionada
    conta_receber = models.ForeignKey(
        ContaReceber, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    conta_pagar = models.ForeignKey(
        ContaPagar, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Cliente/Fornecedor
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    fornecedor = models.ForeignKey(
        Fornecedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    confirmado = models.BooleanField(default=False)
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    
    # Dados do documento (se aplicável)
    numero_documento = models.CharField(max_length=50, blank=True)
    
    # Dados do cheque (se aplicável)
    numero_cheque = models.CharField(max_length=20, blank=True)
    banco_cheque = models.CharField(max_length=100, blank=True)
    emissor_cheque = models.CharField(max_length=200, blank=True)
    data_cheque = models.DateField(null=True, blank=True)
    

    
    # Dados do cartão (se aplicável)
    numero_cartao_mascarado = models.CharField(max_length=20, blank=True)
    bandeira_cartao = models.CharField(max_length=50, blank=True)
    numero_autorizacao = models.CharField(max_length=20, blank=True)
    numero_comprovante = models.CharField(max_length=30, blank=True)
    
    # Movimento de estorno (se aplicável)
    movimento_original = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='estornos',
        help_text="Movimento original que está sendo estornado"
    )
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Movimento de Caixa"
        verbose_name_plural = "Movimentos de Caixa"
        indexes = [
            models.Index(fields=['data_movimento', 'loja']),
            models.Index(fields=['tipo_movimento', 'status']),
            models.Index(fields=['usuario', 'data_movimento']),
            models.Index(fields=['venda_relacionada']),
        ]
        ordering = ['-data_movimento', '-hora_movimento']
    
    def __str__(self):
        sinal = '+' if self.valor >= 0 else ''
        return f"{self.data_movimento} - {sinal}R$ {self.valor} - {self.get_tipo_movimento_display()}"
    
    def save(self, *args, **kwargs):
        # Gerar número do movimento se não existir
        if not self.numero_movimento:
            hoje = date.today()
            prefixo = f"CX{hoje.strftime('%Y%m%d')}"
            
            ultimo_numero = MovimentoCaixa.objects.filter(
                numero_movimento__startswith=prefixo,
                loja=self.loja
            ).count() + 1
            
            self.numero_movimento = f"{prefixo}{ultimo_numero:04d}"
        
        super().save(*args, **kwargs)
    
    def confirmar_movimento(self, usuario_confirmacao=None):
        """Confirma o movimento de caixa"""
        if self.confirmado:
            raise ValidationError("Movimento já confirmado")
        
        self.confirmado = True
        self.status = 'confirmado'
        self.data_confirmacao = datetime.now()
        self.save()
        
        # Se for movimento de venda, criar/atualizar movimentação financeira
        if self.tipo_movimento == 'venda' and self.venda_relacionada:
            self._criar_movimentacao_financeira()
    
    def estornar_movimento(self, motivo="", usuario_estorno=None):
        """Estorna o movimento de caixa"""
        if not self.confirmado:
            raise ValidationError("Apenas movimentos confirmados podem ser estornados")
        
        if self.status == 'estornado':
            raise ValidationError("Movimento já estornado")
        
        # Criar movimento de estorno
        MovimentoCaixa.objects.create(
            tipo_movimento='cancelamento',
            forma_pagamento=self.forma_pagamento,
            valor=-self.valor,  # Valor oposto
            descricao=f"Estorno: {self.descricao}",
            observacoes=f"Estorno do movimento {self.numero_movimento}. Motivo: {motivo}",
            usuario=usuario_estorno or self.usuario,
            loja=self.loja,
            venda_relacionada=self.venda_relacionada,
            movimento_original=self,
            status='confirmado',
            confirmado=True,
            data_confirmacao=datetime.now(),
            empresa=self.empresa
        )
        
        # Atualizar status do movimento original
        self.status = 'estornado'
        self.observacoes += f"\nEstornado em {datetime.now()}: {motivo}"
        self.save()
    
    def _criar_movimentacao_financeira(self):
        """Cria movimentação financeira correspondente"""
        # Buscar conta principal da empresa
        conta_principal = ContaBancaria.objects.filter(
            empresa=self.empresa,
            conta_principal=True,
            ativa=True
        ).first()
        
        if not conta_principal:
            return  # Sem conta principal, não criar movimentação
        
        # Buscar plano de contas padrão para vendas
        plano_vendas = PlanoContas.objects.filter(
            empresa=self.empresa,
            tipo_conta='receita',
            nome__icontains='venda'
        ).first()
        
        if not plano_vendas:
            return  # Sem plano de contas, não criar movimentação
        
        # Criar movimentação apenas para dinheiro e transferencia (que vão direto para o caixa)
        if self.forma_pagamento in ['dinheiro', 'transferencia']:
            MovimentacaoFinanceira.objects.create(
                tipo_movimentacao='entrada',
                tipo_documento=self.forma_pagamento,
                data_movimentacao=self.data_movimento,
                valor=abs(self.valor),  # Sempre positivo para entrada
                conta_bancaria=conta_principal,
                plano_contas=plano_vendas,
                cliente=self.cliente,
                venda_relacionada=self.venda_relacionada,
                descricao=f"Recebimento venda: {self.descricao}",
                observacoes=f"Movimento caixa: {self.numero_movimento}",
                status='confirmada',
                confirmada=True,
                data_confirmacao=self.data_confirmacao,
                usuario_responsavel=self.usuario,
                empresa=self.empresa
            )
    
    @property
    def valor_liquido(self):
        """Valor líquido (valor - troco)"""
        return self.valor - self.valor_troco
    
    @property
    def eh_entrada(self):
        """Verifica se é uma entrada de caixa"""
        return self.valor > 0
    
    @property
    def eh_saida(self):
        """Verifica se é uma saída de caixa"""
        return self.valor < 0
    
    @classmethod
    def calcular_saldo_caixa(cls, loja, data=None):
        """Calcula saldo atual do caixa"""
        if data is None:
            data = date.today()
        
        movimentos = cls.objects.filter(
            loja=loja,
            data_movimento__lte=data,
            confirmado=True
        )
        
        saldo = movimentos.aggregate(
            total=models.Sum('valor')
        )['total'] or Decimal('0.00')
        
        return saldo
    
    @classmethod
    def obter_ultimo_fechamento(cls, loja):
        """Obtém o último fechamento de caixa da loja"""
        return cls.objects.filter(
            loja=loja,
            tipo_movimento='fechamento',
            confirmado=True
        ).order_by('-data_movimento', '-hora_movimento').first()
    
    @classmethod
    def caixa_esta_aberto(cls, loja, data=None):
        """Verifica se o caixa está aberto"""
        if data is None:
            data = date.today()
        
        # Buscar última abertura e último fechamento do dia
        ultima_abertura = cls.objects.filter(
            loja=loja,
            data_movimento=data,
            tipo_movimento='abertura',
            confirmado=True
        ).order_by('-hora_movimento').first()
        
        ultimo_fechamento = cls.objects.filter(
            loja=loja,
            data_movimento=data,
            tipo_movimento='fechamento',
            confirmado=True
        ).order_by('-hora_movimento').first()
        
        # Se não há abertura, caixa fechado
        if not ultima_abertura:
            return False
        
        # Se não há fechamento, caixa aberto
        if not ultimo_fechamento:
            return True
        
        # Se abertura é posterior ao fechamento, caixa aberto
        return ultima_abertura.hora_movimento > ultimo_fechamento.hora_movimento


####Imposto

class ConfiguracaoImposto(TimeStampedModel):
    """Configurações de impostos por empresa"""
    
    empresa = models.OneToOneField(
        Empresa, 
        on_delete=models.CASCADE,
        related_name='configuracao_impostos'
    )
    
    # Regime tributário
    regime_tributario = models.CharField(
        max_length=20,
        choices=ImpostoTributo.REGIME_TRIBUTARIO_CHOICES,
        default='simples_nacional'
    )
    
    # Simples Nacional
    anexo_simples = models.CharField(
        max_length=10,
        choices=[
            ('anexo_1', 'Anexo I - Comércio'),
            ('anexo_2', 'Anexo II - Indústria'),
            ('anexo_3', 'Anexo III - Serviços'),
            ('anexo_4', 'Anexo IV - Serviços'),
            ('anexo_5', 'Anexo V - Serviços'),
        ],
        default='anexo_1',
        help_text="Anexo do Simples Nacional"
    )
    
    # CNAE principal
    cnae_principal = models.CharField(
        max_length=10,
        help_text="CNAE principal da empresa"
    )
    
    # Alíquotas padrão
    aliquota_pis = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.65'),
        help_text="Alíquota padrão do PIS (%)"
    )
    aliquota_cofins = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('3.00'),
        help_text="Alíquota padrão do COFINS (%)"
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('5.00'),
        help_text="Alíquota padrão do ISS (%)"
    )
    
    # Configurações automáticas
    gerar_impostos_automaticamente = models.BooleanField(
        default=True,
        help_text="Gerar impostos automaticamente no final do mês"
    )
    dia_vencimento_impostos = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia do mês para vencimento dos impostos"
    )
    
    # Observações
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Configuração de Impostos"
        verbose_name_plural = "Configurações de Impostos"
    
    def __str__(self):
        return f"Configuração Impostos - {self.empresa.nome}"


