# apps/comandas/forms.py
from decimal import Decimal
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from .models import (
    CentroRequisicao, Comanda, ItemComanda, ProdutoComanda, Mesa,
    CategoriaComanda, Pagamento, ConfiguracaoComanda
)

class ComandaForm(forms.ModelForm):
    class Meta:
        model = Comanda
        fields = [
            'tipo_atendimento', 'cliente', 'mesa', 'atendente',
            'desconto_percentual', 'taxa_servico', 'observacoes'
        ]
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            from apps.clientes.models import Cliente
            from apps.funcionarios.models import Funcionario
            
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa)
            self.fields['mesa'].queryset = Mesa.objects.filter(empresa=empresa, ativa=True)
            self.fields['atendente'].queryset = Funcionario.objects.filter(
                empresa=empresa, ativo=True
            )

class ItemComandaForm(forms.ModelForm):
    class Meta:
        model = ItemComanda
        fields = ['produto', 'quantidade', 'observacoes']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'min': '1', 'max': '99'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            self.fields['produto'].queryset = ProdutoComanda.objects.filter(
                empresa=empresa, disponivel=True
            )

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = [
            'forma_pagamento', 'valor', 'numero_transacao',
            'numero_autorizacao', 'bandeira_cartao', 'observacoes'
        ]
    
    def __init__(self, *args, **kwargs):
        valor_sugerido = kwargs.pop('valor_sugerido', None)
        super().__init__(*args, **kwargs)
        
        if valor_sugerido:
            self.fields['valor'].initial = valor_sugerido

class ProdutoComandaForm(forms.ModelForm):
    class Meta:
        model = ProdutoComanda
        fields = [
            'nome', 'categoria', 'descricao', 'preco_venda',
            'preco_promocional', 'tempo_preparo_minutos',
            'controla_estoque', 'quantidade_estoque', 'estoque_minimo',
            'calorias', 'ingredientes', 'imagem', 'disponivel', 'destaque'
        ]

class ConfiguracaoComandaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoComanda
        fields = [
            'taxa_servico_percentual', 'taxa_entrega_valor',
            'tempo_limite_preparo', 'tempo_alerta_atraso',
            'permite_desconto', 'desconto_maximo',
            'permite_cancelamento', 'permite_self_service'
        ]

    

    
class CentroRequisicaoForm(forms.ModelForm):
    class Meta:
        model = CentroRequisicao
        fields = [
            'codigo', 'nome',
            'tipo_centro', 'descricao',
            'localizacao', 'andar',
            'responsavel', 'ativo',
            'aceita_pedidos', 'imprime_automatico',
            'impressora_ip', 'impressora_nome', 'horario_inicio',
            'horario_fim', 'ordem_preparo', 'empresa'

        ]

class TemplateComandaForm(forms.ModelForm):
    class Meta:
        fields = [
            'nome', 'descricao', 'tipo_atendimento_padrao',
            'aplica_taxa_servico', 'taxa_servico_personalizada',
            'observacoes_padrao', 'observacoes_cozinha_padrao',
            'ativo', 'empresa', 
        ]


# =====================================
# FORMS PARA MESAS - ADICIONAR AO ARQUIVO EXISTENTE
# =====================================

class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = [
            'numero', 'nome', 'capacidade', 'localizacao', 
            'observacoes', 'permite_self_service', 'ativa'
        ]
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 01, A1, Mesa 1'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da mesa (opcional)'
            }),
            'capacidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20'
            }),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salão principal, Varanda, etc.'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Observações sobre a mesa...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Identificação',
                Row(
                    Column('numero', css_class='form-group col-md-4 mb-0'),
                    Column('nome', css_class='form-group col-md-8 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('capacidade', css_class='form-group col-md-6 mb-0'),
                    Column('localizacao', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Configurações',
                Row(
                    Column('permite_self_service', css_class='form-group col-md-6 mb-0'),
                    Column('ativa', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'observacoes',
            ),
            Submit('submit', 'Salvar Mesa', css_class='btn btn-primary')
        )
    
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if not numero:
            raise forms.ValidationError('Número da mesa é obrigatório')
        
        # Verificar se número já existe (exceto para edição)
        if self.instance.pk:  # Editando
            existe = Mesa.objects.filter(
                numero=numero,
                empresa=self.instance.empresa
            ).exclude(pk=self.instance.pk).exists()
        else:  # Criando novo
            # Não podemos verificar empresa aqui pois ainda não foi definida
            pass
        
        return numero.upper().strip()

class OcuparMesaForm(forms.Form):
    criar_comanda = forms.BooleanField(
        required=False,
        initial=True,
        label="Criar comanda automaticamente",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=None,  # Será definido no __init__
        required=False,
        empty_label="Cliente não identificado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    atendente = forms.ModelChoiceField(
        queryset=None,  # Será definido no __init__
        required=False,
        empty_label="Usuário atual",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Observações sobre a ocupação...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            from apps.clientes.models import Cliente
            from apps.funcionarios.models import Funcionario
            
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa)
            self.fields['atendente'].queryset = Funcionario.objects.filter(
                empresa=empresa, ativo=True
            )
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'criar_comanda',
            Fieldset(
                'Dados da Comanda',
                'cliente',
                'atendente',
                'observacoes',
                css_class='comanda-fields'
            ),
            Submit('submit', 'Ocupar Mesa', css_class='btn btn-success')
        )

class ReservarMesaForm(forms.Form):
    cliente_reserva = forms.CharField(
        max_length=200,
        label="Nome do Cliente",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo do cliente'
        })
    )
    
    telefone_reserva = forms.CharField(
        max_length=20,
        required=False,
        label="Telefone de Contato",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999'
        })
    )
    
    data_hora_reserva = forms.DateTimeField(
        required=False,
        label="Data e Hora da Reserva",
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        help_text="Deixe em branco para reserva imediata"
    )
    
    observacoes_reserva = forms.CharField(
        required=False,
        label="Observações",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Observações sobre a reserva...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'cliente_reserva',
            Row(
                Column('telefone_reserva', css_class='form-group col-md-6 mb-0'),
                Column('data_hora_reserva', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'observacoes_reserva',
            Submit('submit', 'Reservar Mesa', css_class='btn btn-warning')
        )

class LiberarMesaForm(forms.Form):
    novo_status = forms.ChoiceField(
        choices=[
            ('livre', 'Livre'),
            ('limpeza', 'Em Limpeza'),
            ('manutencao', 'Manutenção'),
        ],
        initial='livre',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    forcar_liberacao = forms.BooleanField(
        required=False,
        label="Forçar liberação (cancelar comandas abertas)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Motivo da liberação...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'novo_status',
            'observacoes',
            HTML('<div class="alert alert-warning mt-3">'),
            'forcar_liberacao',
            HTML('<small class="form-text text-muted">Atenção: Forçar liberação irá cancelar todas as comandas abertas desta mesa!</small>'),
            HTML('</div>'),
            Submit('submit', 'Liberar Mesa', css_class='btn btn-danger')
        )

class FiltroMesaForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Mesa.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    capacidade_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'min': '1',
            'placeholder': 'Mín.'
        })
    )
    
    capacidade_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'min': '1',
            'placeholder': 'Máx.'
        })
    )
    
    localizacao = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Localização...'
        })
    )
    
    ativa = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('true', 'Ativas'),
            ('false', 'Inativas')
        ],
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    permite_self_service = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class DescontoForm(forms.Form):
    valor = forms.DecimalField(
        label="Valor do Desconto",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Digite o valor do desconto"
        })
    )
    motivo = forms.CharField(
        label="Motivo do Desconto",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ex: cliente especial, promoção..."
        })
    )


class AcrescimoForm(forms.Form):
    valor = forms.DecimalField(
        label="Valor do Acréscimo",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Digite o valor do acréscimo"
        })
    )
    motivo = forms.CharField(
        label="Motivo do Acréscimo",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ex: serviço extra, taxa adicional..."
        })
    )


class GorjetaForm(forms.Form):
    percentual = forms.DecimalField(
        label="Percentual da Gorjeta (%)",
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=Decimal("100.00"),
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Ex: 10"
        })
    )

    def clean_percentual(self):
        percentual = self.cleaned_data["percentual"]
        if percentual > Decimal("30.00"):
            raise forms.ValidationError("A gorjeta não pode ser superior a 30%.")
        return percentual


class DividirContaForm(forms.Form):
    quantidade_pessoas = forms.IntegerField(
        label="Quantidade de Pessoas",
        min_value=2,
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Ex: 2"
        })
    )

    def clean_quantidade_pessoas(self):
        qtd = self.cleaned_data["quantidade_pessoas"]
        if qtd > 50:
            raise forms.ValidationError("Não é permitido dividir a conta para mais de 50 pessoas.")
        return qtd



