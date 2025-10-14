# apps/comandas/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, Empresa, Usuario, Loja
from apps.clientes.models import Cliente
from apps.funcionarios.models import Funcionario
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
import uuid

class CategoriaComanda(TimeStampedModel):
    """Categorias de produtos para comandas"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    cor_exibicao = models.CharField(
        max_length=7, 
        default="#007bff",
        help_text="Cor em hexadecimal para exibição"
    )
    icone = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Classe do ícone (FontAwesome, ex: fas fa-coffee)"
    )
    ordem_exibicao = models.IntegerField(default=0)
    ativa = models.BooleanField(default=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Categoria de Comanda"
        verbose_name_plural = "Categorias de Comandas"
        ordering = ['ordem_exibicao', 'nome']
        unique_together = [['nome', 'empresa']]
    
    def __str__(self):
        return self.nome

class CentroRequisicao(TimeStampedModel):
    """Centros de requisição (Cozinha, Bar, etc.)"""
    TIPO_CENTRO_CHOICES = [
        ('cozinha', 'Cozinha'),
        ('bar', 'Bar'),
        ('lanchonete', 'Lanchonete'),
        ('confeitaria', 'Confeitaria'),
        ('chapeiro', 'Chapeiro'),
        ('saladas', 'Saladas'),
        ('bebidas', 'Bebidas'),
        ('sobremesas', 'Sobremesas'),
        ('outros', 'Outros'),
    ]
    
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    tipo_centro = models.CharField(max_length=15, choices=TIPO_CENTRO_CHOICES)
    descricao = models.TextField(blank=True)
    
    # Localização
    localizacao = models.CharField(max_length=200, blank=True)
    andar = models.CharField(max_length=20, blank=True)
    
    # Responsável
    responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='centros_responsavel'
    )
    
    # Configurações
    ativo = models.BooleanField(default=True)
    aceita_pedidos = models.BooleanField(default=True)
    imprime_automatico = models.BooleanField(default=True)
    
    # Impressora associada
    impressora_ip = models.CharField(max_length=15, blank=True)
    impressora_nome = models.CharField(max_length=100, blank=True)
    
    # Horário de funcionamento
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fim = models.TimeField(null=True, blank=True)
    
    # Ordem de prioridade
    ordem_preparo = models.IntegerField(default=0)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Centro de Requisição"
        verbose_name_plural = "Centros de Requisição"
        unique_together = [['codigo', 'empresa']]
        ordering = ['ordem_preparo', 'nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def esta_funcionando(self):
        """Verifica se centro está em horário de funcionamento"""
        if not self.horario_inicio or not self.horario_fim:
            return True  # Sem restrição de horário
        
        from datetime import time
        now = timezone.now().time()
        return self.horario_inicio <= now <= self.horario_fim
    
    def itens_pendentes_count(self):
        """Conta itens pendentes neste centro"""
        return ItemComanda.objects.filter(
            produto__centro_requisicao=self,
            status__in=['pendente', 'em_preparo']
        ).count()


class ProdutoComanda(TimeStampedModel):
    """Produtos disponíveis para comandas"""
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(CategoriaComanda, on_delete=models.PROTECT)
    
    centro_requisicao = models.ForeignKey(
        CentroRequisicao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Centro responsável pelo preparo deste item"
    )

    # Preços
    preco_venda = models.DecimalField(max_digits=8, decimal_places=2)
    preco_promocional = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Configurações
    disponivel = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    tempo_preparo_minutos = models.IntegerField(
        default=10,
        help_text="Tempo estimado de preparo em minutos"
    )
    
    # Controle de estoque (opcional)
    controla_estoque = models.BooleanField(default=False)
    quantidade_estoque = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=0)
    
    # Informações nutricionais/extras
    calorias = models.IntegerField(null=True, blank=True)
    ingredientes = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    
    # Imagem
    imagem = models.ImageField(
        upload_to='comandas/produtos/', 
        null=True, 
        blank=True
    )
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Produto de Comanda"
        verbose_name_plural = "Produtos de Comandas"
        ordering = ['categoria', 'nome']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['categoria', 'disponivel']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._gerar_codigo()
        super().save(*args, **kwargs)
    
    def _gerar_codigo(self):
        """Gera código único para o produto"""
        prefixo = self.categoria.nome[:3].upper()
        contador = ProdutoComanda.objects.filter(
            empresa=self.empresa,
            codigo__startswith=prefixo
        ).count() + 1
        return f"{prefixo}{contador:04d}"
    
    @property
    def preco_atual(self):
        """Retorna preço promocional se houver, senão preço normal"""
        return self.preco_promocional if self.preco_promocional else self.preco_venda
    
    @property
    def em_promocao(self):
        """Verifica se produto está em promoção"""
        return self.preco_promocional is not None and self.preco_promocional > 0
    
    def baixar_estoque(self, quantidade):
        """Baixa estoque do produto"""
        if self.controla_estoque:
            if self.quantidade_estoque >= quantidade:
                self.quantidade_estoque -= quantidade
                self.save()
            else:
                raise ValidationError(f"Estoque insuficiente. Disponível: {self.quantidade_estoque}")

class Mesa(TimeStampedModel):
    """Mesas do estabelecimento"""
    STATUS_CHOICES = [
        ('livre', 'Livre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('limpeza', 'Em Limpeza'),
        ('manutencao', 'Manutenção'),
    ]
    
    numero = models.CharField(max_length=10)
    nome = models.CharField(max_length=100, blank=True)
    capacidade = models.IntegerField(default=4)
    localizacao = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='livre')
    observacoes = models.TextField(blank=True)
    
    # QR Code para self-service (opcional)
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True)
    permite_self_service = models.BooleanField(default=False)
    
    ativa = models.BooleanField(default=True)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        unique_together = [['numero', 'loja']]
        ordering = ['numero']
    
    def __str__(self):
        return f"Mesa {self.numero}" + (f" - {self.nome}" if self.nome else "")
    
    def ocupar_mesa(self):
        """Ocupa a mesa"""
        if self.status != 'livre':
            raise ValidationError(f"Mesa não está livre. Status atual: {self.get_status_display()}")
        self.status = 'ocupada'
        self.save()
    
    def liberar_mesa(self):
        """Libera a mesa"""
        self.status = 'livre'
        self.save()

class Comanda(TimeStampedModel):
    """Comanda principal"""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_preparo', 'Em Preparo'),
        ('pronta', 'Pronta'),
        ('entregue', 'Entregue'),
        ('fechada', 'Fechada'),
        ('cancelada', 'Cancelada'),
    ]
    
    TIPO_ATENDIMENTO_CHOICES = [
        ('balcao', 'Balcão'),
        ('mesa', 'Mesa'),
        ('delivery', 'Delivery'),
        ('retirada', 'Retirada'),
    ]
    
    # Identificação
    numero_comanda = models.CharField(max_length=20, unique=True)
    tipo_atendimento = models.CharField(max_length=15, choices=TIPO_ATENDIMENTO_CHOICES)
    
    # Relacionamentos
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    atendente = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='comandas_atendidas'
    )
    
    # Datas e horários
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    tempo_estimado_preparo = models.IntegerField(
        default=0,
        help_text="Tempo estimado total em minutos"
    )
    
    # Valores
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto_valor = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_servico = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='aberta')
    observacoes = models.TextField(blank=True)
    observacoes_cozinha = models.TextField(blank=True)
    
    # Entrega (para delivery)
    endereco_entrega = models.TextField(blank=True)
    telefone_contato = models.CharField(max_length=20, blank=True)
    taxa_entrega = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Comanda"
        verbose_name_plural = "Comandas"
        ordering = ['-data_abertura']
        indexes = [
            models.Index(fields=['numero_comanda']),
            models.Index(fields=['status', 'data_abertura']),
            models.Index(fields=['atendente', 'data_abertura']),
        ]
    
    def __str__(self):
        return f"Comanda {self.numero_comanda}"
    
    def save(self, *args, **kwargs):
        if not self.numero_comanda:
            self.numero_comanda = self._gerar_numero_comanda()
        
        # Calcular valores
        self._calcular_valores()
        
        super().save(*args, **kwargs)
    
    def _gerar_numero_comanda(self):
        """Gera número único da comanda"""
        hoje = date.today()
        prefixo = hoje.strftime('%d%m%y')
        
        ultimo_numero = Comanda.objects.filter(
            numero_comanda__startswith=prefixo,
            empresa=self.empresa
        ).count() + 1
        
        return f"{prefixo}{ultimo_numero:04d}"
    
    def _calcular_valores(self):
        """Calcula valores da comanda"""
        # Subtotal dos itens
        self.subtotal = sum(
            item.total for item in self.itens.all()
        )
        
        # Aplicar desconto
        if self.desconto_percentual > 0:
            self.desconto_valor = (self.subtotal * self.desconto_percentual) / 100
        
        # Valor total
        self.total = self.subtotal - self.desconto_valor + self.taxa_servico + self.taxa_entrega
        
        # Tempo estimado total
        self.tempo_estimado_preparo = sum(
            item.produto.tempo_preparo_minutos * item.quantidade 
            for item in self.itens.all()
        )
    
    def adicionar_item(self, produto, quantidade, observacoes=""):
        """Adiciona item à comanda"""
        if self.status not in ['aberta']:
            raise ValidationError("Não é possível adicionar itens a uma comanda fechada")
        
        # Verificar estoque
        if produto.controla_estoque and produto.quantidade_estoque < quantidade:
            raise ValidationError(f"Estoque insuficiente para {produto.nome}")
        
        # Verificar se item já existe
        item_existente = self.itens.filter(produto=produto).first()
        
        if item_existente:
            item_existente.quantidade += quantidade
            item_existente.observacoes += f"\n{observacoes}" if observacoes else ""
            item_existente.save()
        else:
            ItemComanda.objects.create(
                comanda=self,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=produto.preco_atual,
                observacoes=observacoes
            )
        
        # Baixar estoque
        produto.baixar_estoque(quantidade)
        
        # Recalcular valores
        self.save()
    
    def fechar_comanda(self, forma_pagamento="dinheiro"):
        """Fecha a comanda"""
        if self.status != 'entregue':
            raise ValidationError("Comanda deve estar entregue para ser fechada")
        
        self.status = 'fechada'
        self.data_fechamento = timezone.now()
        
        # Liberar mesa se houver
        if self.mesa:
            self.mesa.liberar_mesa()
        
        self.save()
    
    @property
    def total_itens(self):
        """Total de itens na comanda"""
        return sum(item.quantidade for item in self.itens.all())
    
    @property
    def troco(self):
        """Calcula troco"""
        return max(0, self.valor_pago - self.total)
    
    @property
    def tempo_decorrido(self):
        """Tempo decorrido desde abertura"""
        from django.utils import timezone
        return timezone.now() - self.data_abertura

class ItemComanda(TimeStampedModel):
    """Itens da comanda"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_preparo', 'Em Preparo'),
        ('pronto', 'Pronto'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    comanda = models.ForeignKey(
        Comanda, 
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(ProdutoComanda, on_delete=models.PROTECT)
    
    quantidade = models.IntegerField(validators=[MinValueValidator(1)])
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True)
    
    # Tempos
    hora_pedido = models.DateTimeField(auto_now_add=True)
    hora_inicio_preparo = models.DateTimeField(null=True, blank=True)
    hora_finalizacao = models.DateTimeField(null=True, blank=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Item da Comanda"
        verbose_name_plural = "Itens da Comanda"
        ordering = ['hora_pedido']
    
    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade}) - {self.comanda.numero_comanda}"
    
    def save(self, *args, **kwargs):
        self.total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)
        
        # Atualizar valores da comanda
        self.comanda.save()
    
    def iniciar_preparo(self):
        """Inicia preparo do item"""
        if self.status != 'pendente':
            raise ValidationError("Item não está pendente")
        
        self.status = 'em_preparo'
        self.hora_inicio_preparo = timezone.now()
        self.save()
    
    def finalizar_preparo(self):
        """Finaliza preparo do item"""
        if self.status != 'em_preparo':
            raise ValidationError("Item não está em preparo")
        
        self.status = 'pronto'
        self.hora_finalizacao = timezone.now()
        self.save()
    
    def entregar_item(self):
        """Marca item como entregue"""
        if self.status != 'pronto':
            raise ValidationError("Item não está pronto")
        
        self.status = 'entregue'
        self.hora_entrega = timezone.now()
        self.save()
        
        # Verificar se todos os itens foram entregues
        if not self.comanda.itens.exclude(status='entregue').exists():
            self.comanda.status = 'entregue'
            self.comanda.save()

class Pagamento(TimeStampedModel):
    """Pagamentos da comanda"""
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_debito', 'Cartão de Débito'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('transferencia', 'Transferência'),
        ('vale_refeicao', 'Vale Refeição'),
        ('vale_alimentacao', 'Vale Alimentação'),
        ('credito_loja', 'Crédito da Loja'),
    ]
    
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name='pagamentos'
    )
    
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dados específicos do pagamento
    numero_transacao = models.CharField(max_length=100, blank=True)
    numero_autorizacao = models.CharField(max_length=100, blank=True)
    bandeira_cartao = models.CharField(max_length=50, blank=True)
    
    data_pagamento = models.DateTimeField(auto_now_add=True)
    confirmado = models.BooleanField(default=True)
    
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ['-data_pagamento']
    
    def __str__(self):
        return f"{self.get_forma_pagamento_display()} - R$ {self.valor} - {self.comanda.numero_comanda}"

class HistoricoComanda(TimeStampedModel):
    """Histórico de alterações da comanda"""
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name='historico'
    )
    
    acao = models.CharField(max_length=100)
    descricao = models.TextField()
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    data_acao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Histórico da Comanda"
        verbose_name_plural = "Históricos das Comandas"
        ordering = ['-data_acao']
    
    def __str__(self):
        return f"{self.acao} - {self.comanda.numero_comanda}"

class ConfiguracaoComanda(TimeStampedModel):
    """Configurações do sistema de comandas"""
    
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name='config_comandas'
    )
    
    # Configurações gerais
    taxa_servico_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        help_text="Taxa de serviço padrão (%)"
    )
    taxa_entrega_valor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5,
        help_text="Taxa de entrega padrão (R$)"
    )
    
    # Tempo limites
    tempo_limite_preparo = models.IntegerField(
        default=30,
        help_text="Tempo limite para preparo (minutos)"
    )
    tempo_alerta_atraso = models.IntegerField(
        default=20,
        help_text="Alertar atraso após X minutos"
    )
    
    # Configurações de impressão
    imprimir_automatico = models.BooleanField(default=True)
    impressora_cozinha = models.CharField(max_length=100, blank=True)
    impressora_balcao = models.CharField(max_length=100, blank=True)
    
    # Funcionalidades
    permite_desconto = models.BooleanField(default=True)
    desconto_maximo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        help_text="Desconto máximo permitido (%)"
    )
    
    permite_cancelamento = models.BooleanField(default=True)
    permite_self_service = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Configuração de Comandas"
        verbose_name_plural = "Configurações de Comandas"
    
    def __str__(self):
        return f"Configurações - {self.empresa.nome}"


class TemplateComanda(TimeStampedModel):
    """Templates de comandas pré-definidas"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    # Configurações padrão
    tipo_atendimento_padrao = models.CharField(
        max_length=15,
        choices=Comanda.TIPO_ATENDIMENTO_CHOICES,
        default='balcao'
    )
    
    # Valores padrão
    aplica_taxa_servico = models.BooleanField(default=True)
    taxa_servico_personalizada = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Observações padrão
    observacoes_padrao = models.TextField(blank=True)
    observacoes_cozinha_padrao = models.TextField(blank=True)
    
    ativo = models.BooleanField(default=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Template de Comanda"
        verbose_name_plural = "Templates de Comandas"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def criar_comanda(self, atendente, mesa=None, cliente=None):
        """Cria comanda baseada no template"""
        comanda = Comanda.objects.create(
            tipo_atendimento=self.tipo_atendimento_padrao,
            atendente=atendente,
            mesa=mesa,
            cliente=cliente,
            observacoes=self.observacoes_padrao,
            observacoes_cozinha=self.observacoes_cozinha_padrao,
            empresa=self.empresa
        )
        
        # Aplicar taxa de serviço personalizada se houver
        if self.aplica_taxa_servico and self.taxa_servico_personalizada:
            comanda.taxa_servico = self.taxa_servico_personalizada
            comanda.save()
        
        # Adicionar itens do template
        for item_template in self.itens_template.all():
            comanda.adicionar_item(
                produto=item_template.produto,
                quantidade=item_template.quantidade_padrao,
                observacoes=item_template.observacoes_padrao
            )
        
        return comanda

class ItemTemplateComanda(TimeStampedModel):
    """Itens do template de comanda"""
    template = models.ForeignKey(
        TemplateComanda,
        on_delete=models.CASCADE,
        related_name='itens_template'
    )
    produto = models.ForeignKey(ProdutoComanda, on_delete=models.CASCADE)
    quantidade_padrao = models.IntegerField(default=1)
    observacoes_padrao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Item do Template"
        verbose_name_plural = "Itens do Template"
        ordering = ['ordem', 'produto__nome']
    
    def __str__(self):
        return f"{self.produto.nome} (x{self.quantidade_padrao}) - {self.template.nome}"

class MovimentacaoComanda(TimeStampedModel):
    """Movimentações e alterações nas comandas"""
    TIPO_MOVIMENTACAO_CHOICES = [
        ('abertura', 'Abertura'),
        ('adicao_item', 'Adição de Item'),
        ('remocao_item', 'Remoção de Item'),
        ('alteracao_item', 'Alteração de Item'),
        ('aplicacao_desconto', 'Aplicação de Desconto'),
        ('remocao_desconto', 'Remoção de Desconto'),
        ('adicao_taxa', 'Adição de Taxa'),
        ('pagamento', 'Pagamento'),
        ('cancelamento', 'Cancelamento'),
        ('fechamento', 'Fechamento'),
        ('transferencia_mesa', 'Transferência de Mesa'),
        ('divisao_conta', 'Divisão de Conta'),
        ('outros', 'Outros'),
    ]
    
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name='movimentacoes'
    )
    
    tipo_movimentacao = models.CharField(max_length=20, choices=TIPO_MOVIMENTACAO_CHOICES)
    descricao = models.TextField()
    
    # Valores envolvidos
    valor_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    valor_atual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    valor_alteracao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Dados relacionados
    item_relacionado = models.ForeignKey(
        ItemComanda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pagamento_relacionado = models.ForeignKey(
        Pagamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Dados JSON para informações extras
    dados_extras = models.JSONField(default=dict, blank=True)
    
    # Usuário responsável
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    
    # IP e dispositivo (para auditoria)
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Movimentação da Comanda"
        verbose_name_plural = "Movimentações das Comandas"
        ordering = ['-data_movimentacao']
        indexes = [
            models.Index(fields=['comanda', 'data_movimentacao']),
            models.Index(fields=['tipo_movimentacao', 'data_movimentacao']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_movimentacao_display()} - {self.comanda.numero_comanda}"
    
    @classmethod
    def registrar_movimentacao(cls, comanda, tipo_movimentacao, descricao, 
                             usuario=None, valor_anterior=None, valor_atual=None,
                             item_relacionado=None, pagamento_relacionado=None, 
                             dados_extras=None, request=None):
        """Registra uma movimentação na comanda"""
        
        # Calcular valor da alteração
        valor_alteracao = None
        if valor_anterior is not None and valor_atual is not None:
            valor_alteracao = valor_atual - valor_anterior
        
        # Capturar dados da requisição se disponível
        ip_origem = None
        user_agent = ""
        if request:
            ip_origem = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            comanda=comanda,
            tipo_movimentacao=tipo_movimentacao,
            descricao=descricao,
            valor_anterior=valor_anterior,
            valor_atual=valor_atual,
            valor_alteracao=valor_alteracao,
            item_relacionado=item_relacionado,
            pagamento_relacionado=pagamento_relacionado,
            dados_extras=dados_extras or {},
            usuario=usuario,
            ip_origem=ip_origem,
            user_agent=user_agent
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Obtém IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip




