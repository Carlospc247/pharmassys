from django import forms
from django.forms import inlineformset_factory
from .models import Compra, ItemCompra
from apps.produtos.models import Produto
from apps.fornecedores.models import Fornecedor

class CompraForm(forms.ModelForm):
    """
    Formulário principal para os dados da Compra (o cabeçalho).
    """
    # Adicionamos um campo de fornecedor com queryset para garantir que apenas
    # fornecedores ativos sejam selecionáveis.
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Compra
        fields = ['fornecedor']
        # O campo 'data' é preenchido automaticamente, então não o incluímos.


class ItemCompraForm(forms.ModelForm):
    """
    Formulário para cada linha de item da compra.
    """
    # Usamos ModelChoiceField para ter um dropdown de produtos.
    # Numa view mais avançada, isto seria substituído por um campo de busca (autocomplete).
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True).order_by('nome_comercial'),
        widget=forms.Select(attrs={'class': 'form-select item-produto'})
    )

    class Meta:
        model = ItemCompra
        fields = ['produto', 'quantidade', 'preco_unitario']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'class': 'form-control item-quantidade', 'min': '0.01', 'step': '0.01'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control item-preco', 'min': '0.01', 'step': '0.01'}),
        }

# O 'FormSet' é a magia que permite ter múltiplos formulários de 'ItemCompra'
# ligados a um único formulário de 'Compra'.
ItemCompraFormSet = inlineformset_factory(
    Compra,                  # Modelo pai
    ItemCompra,              # Modelo filho (inline)
    form=ItemCompraForm,     # Formulário a ser usado para cada item
    extra=1,                 # Começa com 1 formulário de item em branco
    can_delete=True,         # Permite que os utilizadores apaguem itens
    can_delete_extra=True
)

