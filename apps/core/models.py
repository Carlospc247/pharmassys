# apps/core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser





class TimeStampedModel(models.Model):
    """Modelo base com timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Empresa(models.Model):
    """Empresa cliente que usa o sistema"""
    # Dados básicos
    nome = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    nif = models.CharField(max_length=10, unique=True)
    
    # Endereço
    endereco = models.CharField(max_length=200)
    numero = models.CharField(max_length=10, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    provincia = models.CharField(max_length=50, choices=[
        ('BGO', 'Bengo'),
        ('ICB', 'Icolo e Bengo'),
        ('BGU', 'Benguela'),
        ('BIE', 'Bié'),
        ('CAB', 'Cabinda'),
        ('CCS', 'Cuando Cubango'),
        ('CNO', 'Cuanza Norte'),
        ('CUS', 'Cuanza Sul'),
        ('CNN', 'Cunene'),
        ('HUA', 'Huambo'),
        ('HUI', 'Huíla'),
        ('LUA', 'Luanda'),
        ('LNO', 'Lunda Norte'),
        ('LSU', 'Lunda Sul'),
        ('MAL', 'Malanje'),
        ('MOX', 'Moxico'),
        ('NAM', 'Namibe'),
        ('UIG', 'Uíge'),
        ('ZAI', 'Zaire'),
    ])

    postal = models.CharField(max_length=9)
    
    
    # Contato
    telefone = models.CharField(max_length=20)
    email = models.EmailField()

    foto = models.ImageField(upload_to='core/empresa/', null=True, blank=True, default='https://res.cloudinary.com/drb9m2gwz/image/upload/v1762087442/logo_wovikm.png')

    # Status
    ativa = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        
    def __str__(self):
        return self.nome


class Loja(TimeStampedModel):
    """Loja/Filial da empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lojas')
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20)
    
    # Endereço
    endereco = models.CharField(max_length=200)
    numero = models.CharField(max_length=10, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    postal = models.CharField(max_length=9)
    provincia = models.CharField(max_length=50, choices=[
        ('BGO', 'Bengo'),
        ('ICB', 'Icolo e Bengo'),
        ('BGU', 'Benguela'),
        ('BIE', 'Bié'),
        ('CAB', 'Cabinda'),
        ('CCS', 'Cuando Cubango'),
        ('CNO', 'Cuanza Norte'),
        ('CUS', 'Cuanza Sul'),
        ('CNN', 'Cunene'),
        ('HUA', 'Huambo'),
        ('HUI', 'Huíla'),
        ('LUA', 'Luanda'),
        ('LNO', 'Lunda Norte'),
        ('LSU', 'Lunda Sul'),
        ('MAL', 'Malanje'),
        ('MOX', 'Moxico'),
        ('NAM', 'Namibe'),
        ('UIG', 'Uíge'),
        ('ZAI', 'Zaire'),
    ])

    foto = models.ImageField(upload_to='core/loja/', null=True, blank=True, default='https://res.cloudinary.com/drb9m2gwz/image/upload/v1762087442/logo_wovikm.png')

    
    # Contato
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Status
    ativa = models.BooleanField(default=True)
    eh_matriz = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        unique_together = ['empresa', 'codigo']
        
    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"


class Usuario(AbstractUser):
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='usuarios',
        null=True,
        blank=True
    )
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    telefone = models.CharField(max_length=20, blank=True)
    
    # Campo de permissão essencial movido para aqui:
    e_administrador_empresa = models.BooleanField(
        "É Administrador da Empresa?",
        default=False,
        help_text="Se marcado, este utilizador pode gerir todas as lojas e utilizadores da sua empresa."
    )

    foto = models.ImageField(upload_to='core/usuario/', null=True, blank=True, default='https://res.cloudinary.com/drb9m2gwz/image/upload/v1762087442/logo_wovikm.png')


    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return self.username
    

class Categoria(TimeStampedModel ):
    """Categoria de produtos, específica para cada empresa"""
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='categorias'
    )
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, blank=True)
    descricao = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nome'], name='unique_categoria_empresa_nome')
        ]
        ordering = ['nome']

        
    def __str__(self):
        return self.nome


from django.db import models

class ContadorDocumento(models.Model):
    """
    Controla o último número emitido para cada tipo de documento fiscal, 
    garantindo a sequencialidade por Empresa e Ano.
    """
    TIPO_CHOICES = [
        ('FR', 'Fatura Recibo'),        # Venda à vista (PDV)
        ('FT', 'Fatura'),               # Venda a crédito (Cria dívida)
        ('REC', 'Recibo'),              # Liquidação de dívida (Recebimento)
        ('PP', 'Fatura Proforma'),      # Orçamento
        ('NC', 'Nota de Crédito'),
        ('ND', 'Nota de Débito'),  
        ('DT', 'Documento de Transporte'),
        ('VD', 'Venda a Dinheiro'),
        ('TV', 'Talão de Venda'),
        ('TD', 'Talão de Devolução'),
        ('AA', 'Alienação de Ativos'),
        ('DA', 'Devolução de Ativos'),
        ('RP', 'Prémio ou Penalização'),
        ('RE', 'Estorno ou Anulação'),
        ('CS', 'Imputação a Co-Produtos'),
        ('LD', 'Lançamentos Diversos'),
        ('RA', 'Resseguro Aceite'),
        ('RC', 'Resseguro Cedido'),
    ]

    empresa = models.ForeignKey('core.Empresa', on_delete=models.CASCADE)
    tipo_documento = models.CharField(max_length=5, choices=TIPO_CHOICES, unique=True, verbose_name="Tipo de Documento")
    ano = models.IntegerField(default=2025) # Ajustar para o ano atual dinamicamente
    ultimo_numero = models.IntegerField(default=0)
    
    class Meta:
        # Garante que só pode haver uma entrada por Tipo, Empresa e Ano.
        unique_together = ('empresa', 'tipo_documento', 'ano')
        verbose_name = 'Contador de Documento'
        verbose_name_plural = 'Contadores de Documentos'

    def __str__(self):
        return f"Série {self.tipo_documento} de {self.empresa.nome} ({self.ano}): {self.ultimo_numero}"


