# apps/licenca/models.py
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import uuid
from apps.core.models import Empresa, TimeStampedModel

class PlanoLicenca(TimeStampedModel):
    """Tipos de plano disponíveis"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    limite_usuarios = models.IntegerField()
    limite_produtos = models.IntegerField(null=True, blank=True)
    
    # Funcionalidades
    inclui_pdv = models.BooleanField(default=True)
    inclui_estoque = models.BooleanField(default=True)
    inclui_financeiro = models.BooleanField(default=False)
    inclui_relatorios = models.BooleanField(default=False)
    inclui_backup = models.BooleanField(default=False)
    
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Plano de Licença'
        verbose_name_plural = 'Planos de Licença'
    
    def __str__(self):
        return self.nome

class Licenca(TimeStampedModel):
    """Licença de uso do sistema"""
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('expirada', 'Expirada'),
        ('suspensa', 'Suspensa'),
        ('cancelada', 'Cancelada'),
    ]
    
    chave_licenca = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='licenca')
    plano = models.ForeignKey(PlanoLicenca, on_delete=models.PROTECT)
    
    data_inicio = models.DateField(default=timezone.now)
    data_vencimento = models.DateField()
    data_cancelamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativa')
    
    class Meta:
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'
        
    def __str__(self):
        return f"{self.empresa.nome} - {self.plano.nome}"
    
    @property
    def esta_vencida(self):
        return self.data_vencimento < timezone.now().date()
    
    @property
    def dias_para_vencer(self):
        delta = self.data_vencimento - timezone.now().date()
        return delta.days
    
    def renovar(self, meses=1):
        if self.esta_vencida:
            self.data_vencimento = timezone.now().date() + timedelta(days=30 * meses)
        else:
            self.data_vencimento += timedelta(days=30 * meses)
        self.status = 'ativa'
        self.save()

class HistoricoLicenca(TimeStampedModel):
    """Histórico de alterações na licença"""
    licenca = models.ForeignKey(Licenca, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=100)
    data_anterior = models.DateField(null=True, blank=True)
    data_nova = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        verbose_name = 'Histórico de Licença'
        verbose_name_plural = 'Histórico de Licenças'
    
    def __str__(self):
        return f"{self.licenca.empresa.nome} - {self.acao}"

