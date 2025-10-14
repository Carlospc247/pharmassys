from django.contrib import admin
from .models import Compra, ItemCompra


class ItemCompraInline(admin.TabularInline):
    """
    Define a interface para adicionar/editar Itens de Compra 
    diretamente na página da Compra.
    """
    model = ItemCompra
    # Campos que aparecerão na linha do inline
    fields = ('produto', 'quantidade', 'preco_unitario', 'display_subtotal')
    # Campo calculado, não pode ser editado
    readonly_fields = ('display_subtotal',)
    # Usa um campo de busca para produtos, essencial para performance
    autocomplete_fields = ('produto',)
    # Começa com uma linha em branco para adicionar um novo item
    extra = 1

    @admin.display(description='Subtotal')
    def display_subtotal(self, obj):
        """Exibe o subtotal calculado na linha do item."""
        if obj.pk:  # Apenas mostra o subtotal se o item já foi salvo
            return f"AKZ {obj.subtotal:,.2f}"
        return "---"


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    """
    Interface de administração avançada para o modelo de Compra.
    """
    # Adiciona a gestão de Itens de Compra na mesma página
    inlines = [ItemCompraInline]
    
    # --- Configuração da Lista de Compras ---
    list_display = ('id', 'fornecedor', 'data', 'display_total')
    list_filter = ('data', 'fornecedor')
    search_fields = ('id', 'fornecedor__nome', 'itens__produto__nome_comercial')
    date_hierarchy = 'data'
    list_per_page = 20

    # --- Configuração do Formulário de Edição ---
    readonly_fields = ('display_total',)
    autocomplete_fields = ('fornecedor',)
    
    fieldsets = (
        (None, {
            'fields': ('fornecedor', 'data', 'display_total')
        }),
    )

    @admin.display(description='Total da Compra', ordering='data') # A ordenação pode ser baseada noutro campo
    def display_total(self, obj):
        """Exibe o total da compra na lista e no formulário."""
        return f"AKZ {obj.total():,.2f}"

