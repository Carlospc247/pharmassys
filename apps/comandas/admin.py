# apps/comandas/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CategoriaComanda, ProdutoComanda, Mesa, Comanda,
    ItemComanda, Pagamento, HistoricoComanda, ConfiguracaoComanda
)

@admin.register(CategoriaComanda)
class CategoriaComandaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cor_preview', 'icone', 'ordem_exibicao', 'ativa', 'empresa']
    list_filter = ['ativa', 'empresa']
    search_fields = ['nome', 'descricao']
    list_editable = ['ordem_exibicao', 'ativa']
    ordering = ['empresa', 'ordem_exibicao', 'nome']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'empresa')
        }),
        ('Aparência', {
            'fields': ('cor_exibicao', 'icone', 'ordem_exibicao')
        }),
        ('Status', {
            'fields': ('ativa',)
        }),
    )
    
    def cor_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor_exibicao
        )
    cor_preview.short_description = 'Cor'

@admin.register(ProdutoComanda)
class ProdutoComandaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'categoria', 'preco_atual_display', 
        'disponivel', 'destaque', 'estoque_display', 'empresa'
    ]
    list_filter = ['categoria', 'disponivel', 'destaque', 'controla_estoque', 'empresa']
    search_fields = ['codigo', 'nome', 'descricao']
    list_editable = ['disponivel', 'destaque']
    ordering = ['categoria', 'nome']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao', 'categoria', 'empresa')
        }),
        ('Preços', {
            'fields': ('preco_venda', 'preco_promocional')
        }),
        ('Configurações', {
            'fields': ('disponivel', 'destaque', 'tempo_preparo_minutos')
        }),
        ('Estoque', {
            'fields': ('controla_estoque', 'quantidade_estoque', 'estoque_minimo'),
            'classes': ('collapse',)
        }),
        ('Informações Extras', {
            'fields': ('calorias', 'ingredientes', 'observacoes', 'imagem'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['codigo']
    
    def preco_atual_display(self, obj):
        if obj.em_promocao:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">R$ {}</span><br>'
                '<strong style="color: #e74c3c;">R$ {}</strong>',
                obj.preco_venda,
                obj.preco_promocional
            )
        return f'R$ {obj.preco_venda}'
    preco_atual_display.short_description = 'Preço'
    
    def estoque_display(self, obj):
        if not obj.controla_estoque:
            return '-'
        
        cor = '#e74c3c' if obj.quantidade_estoque <= obj.estoque_minimo else '#27ae60'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            cor,
            obj.quantidade_estoque
        )
    estoque_display.short_description = 'Estoque'

class ItemComandaInline(admin.TabularInline):
    model = ItemComanda
    extra = 0
    readonly_fields = ['total', 'hora_pedido']
    fields = ['produto', 'quantidade', 'preco_unitario', 'total', 'status', 'observacoes']

class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0
    readonly_fields = ['data_pagamento']

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nome', 'capacidade', 'status', 'localizacao', 'ativa', 'loja']
    list_filter = ['status', 'ativa', 'loja', 'permite_self_service']
    search_fields = ['numero', 'nome', 'localizacao']
    list_editable = ['status', 'ativa']
    ordering = ['loja', 'numero']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'nome', 'loja')
        }),
        ('Configurações', {
            'fields': ('capacidade', 'localizacao', 'status')
        }),
        ('Self-Service', {
            'fields': ('permite_self_service', 'qr_code'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'ativa')
        }),
    )
    
    readonly_fields = ['qr_code']

@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_comanda', 'tipo_atendimento', 'cliente_display', 
        'mesa', 'atendente', 'status', 'total', 'data_abertura'
    ]
    list_filter = ['status', 'tipo_atendimento', 'data_abertura', 'empresa']
    search_fields = ['numero_comanda', 'cliente__nome', 'mesa__numero']
    readonly_fields = [
        'numero_comanda', 'data_abertura', 'subtotal', 
        'total', 'tempo_estimado_preparo', 'total_itens_display'
    ]
    date_hierarchy = 'data_abertura'
    ordering = ['-data_abertura']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_comanda', 'tipo_atendimento', 'data_abertura')
        }),
        ('Participantes', {
            'fields': ('cliente', 'mesa', 'atendente')
        }),
        ('Valores', {
            'fields': (
                'subtotal', 'desconto_valor', 'desconto_percentual',
                'taxa_servico', 'taxa_entrega', 'total', 'valor_pago'
            )
        }),
        ('Status e Controle', {
            'fields': ('status', 'tempo_estimado_preparo')
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_cozinha')
        }),
        ('Entrega (Delivery)', {
            'fields': ('endereco_entrega', 'telefone_contato'),
            'classes': ('collapse',)
        }),
        ('Resumo', {
            'fields': ('total_itens_display',)
        }),
    )
    
    inlines = [ItemComandaInline, PagamentoInline]
    
    def cliente_display(self, obj):
        if obj.cliente:
            return obj.cliente.nome
        return 'Cliente não identificado'
    cliente_display.short_description = 'Cliente'
    
    def total_itens_display(self, obj):
        return f'{obj.total_itens} itens'
    total_itens_display.short_description = 'Total de Itens'
    
    actions = ['fechar_comandas_selecionadas']
    
    def fechar_comandas_selecionadas(self, request, queryset):
        comandas_fechadas = 0
        for comanda in queryset:
            if comanda.status == 'entregue':
                try:
                    comanda.fechar_comanda()
                    comandas_fechadas += 1
                except:
                    pass
        
        self.message_user(request, f'{comandas_fechadas} comanda(s) fechada(s) com sucesso.')
    fechar_comandas_selecionadas.short_description = 'Fechar comandas selecionadas'

@admin.register(ItemComanda)
class ItemComandaAdmin(admin.ModelAdmin):
    list_display = [
        'comanda', 'produto', 'quantidade', 'preco_unitario',
        'total', 'status', 'hora_pedido'
    ]
    list_filter = ['status', 'produto__categoria', 'hora_pedido']
    search_fields = ['comanda__numero_comanda', 'produto__nome']
    readonly_fields = ['total', 'hora_pedido']
    date_hierarchy = 'hora_pedido'
    ordering = ['-hora_pedido']

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'comanda', 'forma_pagamento', 'valor', 'data_pagamento',
        'confirmado', 'numero_transacao'
    ]
    list_filter = ['forma_pagamento', 'confirmado', 'data_pagamento']
    search_fields = ['comanda__numero_comanda', 'numero_transacao', 'numero_autorizacao']
    readonly_fields = ['data_pagamento']
    date_hierarchy = 'data_pagamento'
    ordering = ['-data_pagamento']

@admin.register(HistoricoComanda)
class HistoricoComandaAdmin(admin.ModelAdmin):
    list_display = ['comanda', 'acao', 'usuario', 'data_acao']
    list_filter = ['acao', 'data_acao']
    search_fields = ['comanda__numero_comanda', 'acao', 'descricao']
    readonly_fields = ['data_acao']
    date_hierarchy = 'data_acao'
    ordering = ['-data_acao']

@admin.register(ConfiguracaoComanda)
class ConfiguracaoComandaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'taxa_servico_percentual', 'taxa_entrega_valor']
    
    fieldsets = (
        ('Taxas Padrão', {
            'fields': ('taxa_servico_percentual', 'taxa_entrega_valor')
        }),
        ('Tempos', {
            'fields': ('tempo_limite_preparo', 'tempo_alerta_atraso')
        }),
        ('Impressão', {
            'fields': ('imprimir_automatico', 'impressora_cozinha', 'impressora_balcao')
        }),
        ('Permissões', {
            'fields': (
                'permite_desconto', 'desconto_maximo',
                'permite_cancelamento', 'permite_self_service'
            )
        }),
    )



