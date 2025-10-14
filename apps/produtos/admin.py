# apps/produtos/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from .models import (
    Fabricante, Produto, 
    Lote, HistoricoPreco
)
from apps.core.models import Categoria


  
@admin.register(Fabricante)
class FabricanteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nif', 'origem', 'cidade', 'provincia', 'telefone', 'ativo']
    list_filter = ['origem', 'provincia', 'ativo']
    search_fields = ['nome', 'nif', 'cidade']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('empresa', 'nome', 'nif')
        }),
        ('Localização', {
            'fields': ('origem', 'cidade', 'provincia')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )


class LoteInline(admin.TabularInline):
    model = Lote
    extra = 0
    fields = ['numero_lote', 'validade', 'quantidade']
    readonly_fields = ['created_at']


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['produto', 'numero_lote', 'data_validade', 'quantidade_atual']
    list_filter = ['data_validade', 'produto__empresa']
    search_fields = ['numero_lote', 'nome_produto']
    list_editable = ['quantidade_atual']
    date_hierarchy = 'data_validade'
    ordering = ['data_validade']

    search_fields = ['numero_lote', 'nome_produto']

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome_produto', 'empresa', 'categoria', 'preco_venda_display', 'estoque_atual', 'ativo']
    list_filter = ['ativo', 'empresa', 'categoria']
    search_fields = ['nome_produto', 'codigo_barras']
    readonly_fields = ['valor_estoque', 'preco_venda_display']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'categoria', 'fornecedor', 'fabricante', 'codigo_interno', 'codigo_barras')
        }),
        ('Dados do Produto', {
            'fields': ('nome_produto',)
        }),
        ('Estoque', {
            'fields': ('estoque_atual', 'estoque_minimo', 'estoque_maximo', 'valor_estoque')
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_venda', 'margem_lucro', 'preco_venda_display')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

    # ✅ CORRETO: Só usar autocomplete_fields para ForeignKey simples
    autocomplete_fields = ['categoria', 'fornecedor', 'fabricante']
    search_fields = ['nome_produto', 'codigo_barras']



@admin.register(HistoricoPreco)
class HistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = [
        'produto', 'created_at', 'preco_custo_anterior', 'preco_custo_novo',
        'preco_venda_anterior', 'preco_venda_novo', 'get_variacao_percentual', 'motivo', 'usuario'
    ]
    list_filter = ['created_at', 'motivo', 'usuario']
    search_fields = ['nome_produto', 'motivo']
    readonly_fields = [
        'produto', 'preco_custo_anterior', 'preco_venda_anterior',
        'preco_custo_novo', 'preco_venda_novo', 'motivo', 'usuario', 'created_at',
        'variacao_custo_percentual', 'variacao_venda_percentual'
    ]
    ordering = ['-created_at']
    
    def get_variacao_percentual(self, obj):
        """Mostra variação percentual do preço"""
        variacao = obj.variacao_venda_percentual
        
        if variacao > 0:
            color = 'green'
            sinal = '+'
        elif variacao < 0:
            color = 'red'
            sinal = ''
        else:
            color = 'black'
            sinal = ''
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{:.1f}%</span>',
            color, sinal, variacao
        )
    get_variacao_percentual.short_description = 'Variação'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


