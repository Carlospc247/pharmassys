# apps/produtos/forms.py
from .models import Produto, Lote, Categoria, Fabricante
from .models import Lote
from django import forms
from apps.core.models import Categoria  # Importa o modelo da app 'core'
from django.core.exceptions import ValidationError
from apps.core.models import Categoria
from .models import Produto, Fabricante
from apps.fornecedores.models import Fornecedor
from django.core.exceptions import ValidationError
from apps.core.models import Categoria
import openpyxl
from openpyxl import Workbook








form_field_classes = (
    "block w-full rounded-lg border-gray-300 bg-gray-50 py-2 px-3 text-gray-800 "
    "shadow-sm transition duration-200 ease-in-out "
    "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 "
    "dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400 "
    "dark:focus:ring-blue-500/50 dark:focus:border-blue-500"
)

checkbox_classes = (
    "h-4 w-4 rounded border-gray-300 bg-gray-100 text-blue-600 "
    "focus:ring-blue-500 focus:ring-offset-0 "
    "dark:bg-gray-600 dark:border-gray-500"
)







class ProdutoForm(forms.ModelForm):
    # Adicione o campo 'margem_lucro' aqui para que ele seja processado pelo formulário
    margem_lucro = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0,
        label="Margem de Lucro (%)",
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex: 20.00'})
    )

    class Meta:
        model = Produto
        fields = [
            'nome_produto', 'codigo_barras', 'codigo_interno',
            'categoria', 'fabricante', 'fornecedor',
            'preco_custo', 'preco_venda', 'margem_lucro', # Adicionamos a margem de lucro
            'estoque_minimo', 'estoque_maximo',
            'ativo', 'foto', 'taxa_iva', 'desconto_percentual'
        ]
        labels = {
            'nome_produto': 'Nome Comercial do Produto',
            'codigo_barras': 'Código de Barras (EAN)',
            'codigo_interno': 'Código Interno / SKU',
            'preco_custo': 'Preço de Custo',
            'preco_venda': 'Preço de Venda ao Público',
            'estoque_minimo': 'Nível Mínimo de Estoque',
            'estoque_maximo': 'Nível Máximo de Estoque',
            'ativo': 'Produto Ativo (disponível para venda)',
            'taxa_iva': 'Escreva a percentagem do IVA',
            'desconto_percentual': 'Escreva a percentagem do desconto promocional',
        }
        widgets = {
            'preco_custo': forms.NumberInput(attrs={'step': '0.01'}),
            'preco_venda': forms.NumberInput(attrs={'step': '0.01'}),
            'foto': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        self.empresa = empresa

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-checkbox' # Substitua com sua classe
            else:
                field.widget.attrs['class'] = 'form-input' # Substitua com sua classe

        if empresa:
            if 'categoria' in self.fields:
                self.fields['categoria'].queryset = Categoria.objects.filter(empresa=empresa, ativa=True)
            if 'fabricante' in self.fields:
                self.fields['fabricante'].queryset = Fabricante.objects.filter(empresa=empresa)
            if 'fornecedor' in self.fields:
                self.fields['fornecedor'].queryset = Fornecedor.objects.filter(empresa=empresa, ativo=True)

        # Lógica para popular o campo 'margem_lucro' do formulário
        # ao editar um produto existente
        if self.instance and self.instance.pk:
            self.fields['margem_lucro'].initial = self.instance.margem_lucro

    def clean(self):
        cleaned_data = super().clean()
        
        # Validar o código interno
        codigo_interno = cleaned_data.get("codigo_interno")
        if codigo_interno and self.empresa:
            queryset = Produto.objects.filter(empresa=self.empresa, codigo_interno=codigo_interno)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error('codigo_interno', 'Já existe um produto com este Código Interno nesta empresa.')


        return cleaned_data                


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = [
            'produto', 
            'numero_lote', 
            'data_validade', 
            'quantidade_inicial', 
            'preco_custo_lote'
        ]
        labels = {
            'produto': 'Produto Associado',
            'numero_lote': 'Número do Lote',
            'data_validade': 'Data de Validade',
            'quantidade_inicial': 'Quantidade de Entrada',
            'preco_custo_lote': 'Preço de Custo por Unidade (neste Lote)',
        }
        widgets = {
            'produto': forms.Select(attrs={'class': form_field_classes}),
            'numero_lote': forms.TextInput(attrs={'class': form_field_classes, 'placeholder': 'Ex: L123456'}),
            'data_validade': forms.DateInput(attrs={'class': form_field_classes, 'type': 'date'}),
            'quantidade_inicial': forms.NumberInput(attrs={'class': form_field_classes, 'placeholder': 'Ex: 100'}),
            'preco_custo_lote': forms.NumberInput(attrs={'class': form_field_classes, 'placeholder': '1500.00', 'step': '0.01'}),
        }



class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'codigo', 'descricao', 'ativa']


    def __init__(self, *args, **kwargs):
        # Captura o argumento 'empresa' enviado pela view
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        self.empresa = empresa # Guarda a empresa para usar na validação
        # ... (lógica de estilização) ...

    def clean_nome(self):
        # Este método impede o IntegrityError
        nome = self.cleaned_data.get('nome')
        if nome and self.empresa:
            queryset = Categoria.objects.filter(empresa=self.empresa, nome__iexact=nome)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Já existe uma categoria com este nome nesta empresa.")
        return nome



from django import forms
from .models import Produto, Fabricante


class ImportarProdutosForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo de Produtos",
        help_text="Selecione um arquivo .xlsx, .xls ou .csv com os produtos.",
        widget=forms.FileInput(attrs={
            'class': (
                'block w-full text-sm text-gray-500 '
                'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 '
                'file:text-sm file:font-semibold file:bg-primary file:text-white '
                'hover:file:bg-secondary'
            ),
            'accept': '.xlsx,.xls,.csv'
        })
    )

    atualizar_existentes = forms.BooleanField(
        label="Atualizar produtos existentes",
        help_text="Se marcado, produtos com o mesmo código de barras serão atualizados.",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'
        })
    )

    validar_apenas = forms.BooleanField(
        label="Apenas validar (não importar)",
        help_text="Se marcado, o sistema apenas validará o arquivo sem importar os dados.",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-secondary shadow-sm focus:border-secondary focus:ring focus:ring-secondary focus:ring-opacity-50'
        })
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')

        if not arquivo:
            raise forms.ValidationError("Nenhum arquivo foi enviado.")

        # Verifica o tamanho
        if arquivo.size > 10 * 1024 * 1024:  # 10MB
            raise forms.ValidationError("O arquivo não pode ultrapassar 10 MB.")

        # Normaliza e obtém a extensão
        nome = getattr(arquivo, 'name', '').lower()
        extensao = nome.split('.')[-1] if '.' in nome else ''

        # Permite tipos seguros
        extensoes_permitidas = ['xlsx', 'xls', 'csv']
        if extensao not in extensoes_permitidas:
            raise forms.ValidationError(
                f"Extensão inválida ({extensao}). Envie apenas arquivos: {', '.join(extensoes_permitidas)}."
            )

        # Corrige o content_type para evitar erro em navegadores diferentes
        content_type = getattr(arquivo, 'content_type', '')
        tipos_permitidos = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        if content_type and content_type not in tipos_permitidos:
            raise forms.ValidationError("Tipo de arquivo não suportado para importação.")

        return arquivo

