# apps/servicos/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import Categoria, TimeStampedModel, Empresa, Usuario, Loja
from apps.clientes.models import Cliente
from apps.funcionarios.models import Funcionario
from apps.produtos.models import Produto
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from apps.core.models import TimeStampedModel, Empresa, Usuario, Categoria, Loja
from apps.clientes.models import Cliente
from apps.funcionarios.models import Funcionario
from cloudinary.models import CloudinaryField



# =====================================
# MODELO 1: O CATÁLOGO DE SERVIÇOS
# =====================================
class Servico(TimeStampedModel):
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='servicos_catalogo')
    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    duracao_padrao_minutos = models.IntegerField(default=30)
    preco_padrao = models.DecimalField(max_digits=10, decimal_places=2)
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Desconto promocional em % (ex: 10 = 10%)"
    )
    iva_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="IVA (%)"
    )
    taxa_iva = models.ForeignKey(
        'fiscal.TaxaIVAAGT',  # modelo da tabela de taxas
        on_delete=models.PROTECT,
        verbose_name="Regime Fiscal (AGT)",
        default=1  # ou algum valor válido
    )

    instrucoes_padrao = models.TextField(blank=True, help_text="Instruções para o cliente ou para o funcionário.")
    ativo = models.BooleanField(default=True)
    
    #foto = models.ImageField(upload_to='servicos/fotos/', null=True, blank=True, default='https://res.cloudinary.com/drb9m2gwz/image/upload/v1762087442/logo_wovikm.png')
    foto = CloudinaryField('foto', blank=True, null=True)


    #campos para Servico
    nome = models.CharField(max_length=255, blank=True, null=True)
    duracao_servico_padrao = models.DurationField(blank=True, null=True)
    instrucoes_servico = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Serviço (Catálogo)"
        verbose_name_plural = "Serviços (Catálogo)"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']

    def __str__(self):
        return self.nome
    
    @property
    def preco_com_desconto(self):
        """Retorna o preço final aplicando desconto, se existir."""
        if self.desconto_percentual > 0:
            return self.preco_padrao * (1 - (self.desconto_percentual / 100))
        return self.preco_padrao
    

    def clean(self):
        if self.desconto_percentual < 0 or self.desconto_percentual > 100:
            raise ValidationError("O desconto deve estar entre 0 e 100%.")


# =====================================
# MODELO 2: OS AGENDAMENTOS
# =====================================
class AgendamentoServico(TimeStampedModel):
    """
    Representa UM AGENDAMENTO específico de um serviço para um cliente.
    """
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('em_andamento', 'Em Andamento'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
        ('faltou', 'Cliente Faltou'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='agendado')
    
    # Relações
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='agendamentos')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='agendamentos_servicos')
    
    # Detalhes do Agendamento
    data_hora = models.DateTimeField()
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)
    
    # Campos de execução
    data_inicio_real = models.DateTimeField(null=True, blank=True)
    data_fim_real = models.DateTimeField(null=True, blank=True)
    resultado = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.servico.nome} para {self.cliente.nome_completo} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"



class NotificacaoAgendamento(TimeStampedModel):
    """Notificações de agendamento"""
    TIPO_NOTIFICACAO_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('ligacao', 'Ligação'),
        ('sistema', 'Sistema'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('enviada', 'Enviada'),
        ('entregue', 'Entregue'),
        ('lida', 'Lida'),
        ('erro', 'Erro'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relacionamentos
    agendamento = models.ForeignKey(
        AgendamentoServico,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Configuração da notificação
    tipo_notificacao = models.CharField(max_length=15, choices=TIPO_NOTIFICACAO_CHOICES)
    dias_antecedencia = models.IntegerField(
        help_text="Quantos dias antes do agendamento enviar"
    )
    
    # Conteúdo
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    
    # Agendamento da notificação
    data_agendada_envio = models.DateTimeField()
    data_envio = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_leitura = models.DateTimeField(null=True, blank=True)
    
    # Status e controle
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    tentativas_envio = models.IntegerField(default=0)
    erro_envio = models.TextField(blank=True)
    
    # Dados de contato utilizados
    email_enviado = models.EmailField(blank=True)
    telefone_enviado = models.CharField(max_length=20, blank=True)
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Notificação de Agendamento"
        verbose_name_plural = "Notificações de Agendamento"
        ordering = ['-data_agendada_envio']
        indexes = [
            models.Index(fields=['data_agendada_envio', 'status']),
            models.Index(fields=['agendamento']),
        ]
    
    def __str__(self):
        # CORRIGIDO: usa self.cliente em vez de self.paciente
        return f"Notificação {self.get_tipo_notificacao_display()} - {self.cliente.nome_completo}"
    
    # ... (método enviar_notificacao continua igual) ...

    def _enviar_email(self):
        """Enviar notificação por email"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        # CORRIGIDO: usa self.cliente em vez de self.paciente
        email = self.cliente.email
        if not email:
            raise Exception("Cliente não possui email cadastrado")
        
        self.email_enviado = email
        
        send_mail(
            subject=self.titulo,
            message=self.mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
    
    def _enviar_sms(self):
        """Enviar notificação por SMS"""
        # CORRIGIDO: usa self.cliente em vez de self.paciente
        telefone = self.cliente.telefone
        if not telefone:
            raise Exception("Cliente não possui telefone cadastrado")
        
        self.telefone_enviado = telefone
        # Aqui seria a integração com API de SMS
        pass
    
    def _enviar_whatsapp(self):
        """Enviar notificação por WhatsApp"""
        # CORRIGIDO: usa self.cliente em vez de self.paciente
        telefone = self.cliente.telefone
        if not telefone:
            raise Exception("Cliente não possui telefone cadastrado")
        
        self.telefone_enviado = telefone
        # Aqui seria a integração com API do WhatsApp
        pass


class ConfiguracaoNotificacao(TimeStampedModel):
    """Configurações de notificação por empresa"""
    
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name='config_notificacoes'
    )
    
    # Notificações ativadas
    email_ativo = models.BooleanField(default=True)
    sms_ativo = models.BooleanField(default=False)
    whatsapp_ativo = models.BooleanField(default=False)
    
    # Dias de antecedência para envio
    dias_notificacao = models.CharField(
        max_length=50,
        default="15,7,3,1",
        help_text="Dias de antecedência separados por vírgula (ex: 15,7,3,1)"
    )
    
    # Horários de envio
    horario_inicio_envio = models.TimeField(default="08:00")
    horario_fim_envio = models.TimeField(default="18:00")
    
    # Templates de mensagem
    template_email_titulo = models.CharField(
        max_length=200,
        default="Lembrete de Consulta - {nome_paciente}"
    )
    template_email_mensagem = models.TextField(
        default="""Olá {nome_paciente},



Este é um lembrete de que você tem uma consulta agendada:

📅 Data: {data_consulta}
🕐 Horário: {hora_consulta}
👨‍⚕️ Profissional: {farmaceutico}
🏥 Tipo de Serviço: {servico}

Por favor, chegue com 15 minutos de antecedência.

Atenciosamente,
{nome_empresa}"""
    )
    
    template_sms_mensagem = models.TextField(
        default="""Lembrete: Consulta em {data_consulta} às {hora_consulta} com {farmaceutico}. Chegue 15min antes. {nome_empresa}"""
    )
    
    # Configurações avançadas
    max_tentativas_envio = models.IntegerField(default=3)
    intervalo_tentativas_horas = models.IntegerField(default=2)
    
    class Meta:
        verbose_name = "Configuração de Notificação"
        verbose_name_plural = "Configurações de Notificações"
    
    def __str__(self):
        return f"Configurações - {self.empresa.nome}"
    
    def get_dias_notificacao_lista(self):
        """Retorna lista de dias de notificação"""
        try:
            return [int(dia.strip()) for dia in self.dias_notificacao.split(',')]
        except:
            return [15, 7, 3, 1]  # Padrão



