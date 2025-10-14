# apps/estoque/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TipoMovimentacao, MovimentacaoEstoque, Inventario, 
    ItemInventario, AlertaEstoque, LocalizacaoEstoque
)

@admin.register(TipoMovimentacao)
class TipoMovimentacaoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'codigo', 'natureza', 'requer_documento', 
        'requer_aprovacao', 'automatico', 'ativo'
    ]
    list_filter = [
        'natureza', 'requer_documento', 'requer_aprovacao', 
        'automatico', 'controla_lote', 'controla_validade', 'ativo'
    ]
    search_fields = ['nome', 'codigo', 'descricao']
    list_editable = ['ativo']
    # ✅ CORRIGIDO: TimeStampedModel usa created_at/updated_at
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'codigo', 'natureza')
        }),
        ('Características', {
            'fields': (
                'requer_documento', 'requer_aprovacao', 'automatico'
            )
        }),
        ('Controle de Estoque', {
            'fields': ('controla_lote', 'controla_validade')
        }),
        ('Descrição', {
            'fields': ('descricao',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'usuario', 'created_at']
    list_filter = ['tipo', 'created_at', 'produto__empresa']
    search_fields = ['produto__nome_comercial', 'motivo', 'observacoes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    autocomplete_fields = ['produto']
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('produto', 'usuario', 'tipo', 'quantidade')
        }),
        ('Detalhes', {
            'fields': ('motivo', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('produto', 'usuario')

class ItemInventarioInline(admin.TabularInline):
    model = ItemInventario
    extra = 0
    readonly_fields = ['divergencia_quantidade', 'valor_divergencia', 'tem_divergencia']
    fields = [
        'produto', 'quantidade_sistema', 'quantidade_contada_1', 
        'quantidade_contada_2', 'quantidade_contada', 'valor_unitario',
        'status', 'divergencia_quantidade', 'observacoes'
    ]
    
    def divergencia_quantidade(self, obj):
        return obj.divergencia_quantidade
    divergencia_quantidade.short_description = 'Divergência'
    
    def valor_divergencia(self, obj):
        return f"AKZ {obj.valor_divergencia:.2f}"
    valor_divergencia.short_description = 'Valor Divergência'


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'inventario', 'produto', 'quantidade_sistema', 'quantidade_contada',
        'divergencia_display', 'status', 'usuario_contagem_1'
    ]
    list_filter = [
        'status', 'inventario__status', 'inventario__empresa',
        'data_contagem_1', 'data_contagem_2'
    ]
    search_fields = [
        'produto__nome_comercial', 'inventario__numero_inventario',
        'observacoes'
    ]
    readonly_fields = [
        'divergencia_quantidade', 'valor_divergencia', 'tem_divergencia',
        'percentual_divergencia', 'data_contagem_1', 'data_contagem_2',
        'created_at', 'updated_at'
    ]
    
    autocomplete_fields = ['produto']
    
    fieldsets = (
        ('Inventário', {
            'fields': ('inventario', 'produto')
        }),
        ('Quantidades', {
            'fields': (
                'quantidade_sistema', 'quantidade_contada_1', 
                'quantidade_contada_2', 'quantidade_contada', 'valor_unitario'
            )
        }),
        ('Divergência', {
            'fields': (
                'divergencia_quantidade', 'valor_divergencia', 
                'percentual_divergencia'
            ),
            'classes': ('collapse',)
        }),
        ('Primeira Contagem', {
            'fields': ('usuario_contagem_1', 'data_contagem_1')
        }),
        ('Segunda Contagem', {
            'fields': ('usuario_contagem_2', 'data_contagem_2')
        }),
        ('Status e Observações', {
            'fields': ('status', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def divergencia_display(self, obj):
        divergencia = obj.divergencia_quantidade
        if divergencia == 0:
            return format_html('<span style="color: green;">✓ OK</span>')
        elif divergencia > 0:
            return format_html('<span style="color: blue;">+{}</span>', divergencia)
        else:
            return format_html('<span style="color: red;">{}</span>', divergencia)
    divergencia_display.short_description = 'Divergência'



@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = [
        'numero_inventario', 'titulo', 'empresa', 'loja', 'status', 
        'data_planejada', 'total_produtos_planejados', 'total_divergencias'
    ]
    list_filter = [
        'status', 'empresa', 'loja', 'data_planejada', 
        'apenas_produtos_ativos', 'apenas_com_estoque', 
        'requer_dupla_contagem'
    ]
    search_fields = ['numero_inventario', 'titulo', 'descricao']
    readonly_fields = [
        'numero_inventario', 'data_inicio', 'data_conclusao',
        'total_produtos_planejados', 'total_produtos_contados',
        'total_divergencias', 'valor_divergencia_total',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'data_planejada'
    
    filter_horizontal = ['categorias', 'responsaveis_contagem']
    inlines = [ItemInventarioInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_inventario', 'titulo', 'descricao')
        }),
        ('Escopo', {
            'fields': (
                'empresa', 'loja', 'categorias', 
                'apenas_produtos_ativos', 'apenas_com_estoque'
            )
        }),
        ('Planejamento', {
            'fields': (
                'data_planejada', 'responsavel_planejamento', 
                'responsaveis_contagem'
            )
        }),
        ('Configurações', {
            'fields': ('requer_dupla_contagem', 'bloqueio_movimentacao')
        }),
        ('Execução', {
            'fields': ('status', 'data_inicio', 'data_conclusao')
        }),
        ('Resultados', {
            'fields': (
                'total_produtos_planejados', 'total_produtos_contados',
                'total_divergencias', 'valor_divergencia_total'
            ),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['iniciar_inventario', 'concluir_inventario']
    
    def iniciar_inventario(self, request, queryset):
        for inventario in queryset:
            try:
                inventario.iniciar_inventario()
                self.message_user(request, f'Inventário {inventario.numero_inventario} iniciado com sucesso.')
            except Exception as e:
                self.message_user(request, f'Erro ao iniciar {inventario.numero_inventario}: {str(e)}', level='error')
    iniciar_inventario.short_description = 'Iniciar inventários selecionados'
    
    def concluir_inventario(self, request, queryset):
        for inventario in queryset:
            try:
                inventario.concluir_inventario()
                self.message_user(request, f'Inventário {inventario.numero_inventario} concluído com sucesso.')
            except Exception as e:
                self.message_user(request, f'Erro ao concluir {inventario.numero_inventario}: {str(e)}', level='error')
    concluir_inventario.short_description = 'Concluir inventários selecionados'


@admin.register(AlertaEstoque)
class AlertaEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        'produto', 'tipo_alerta', 'prioridade', 'quantidade_atual',
        'ativo', 'notificado', 'created_at'
    ]
    list_filter = [
        'tipo_alerta', 'prioridade', 'ativo', 'notificado',
        'empresa', 'loja', 'created_at'
    ]
    search_fields = [
        'produto__nome_comercial', 'titulo', 'descricao',
        'observacoes_resolucao'
    ]
    readonly_fields = ['data_resolucao', 'data_notificacao', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    autocomplete_fields = ['produto', 'lote', 'resolvido_por']
    
    fieldsets = (
        ('Alerta', {
            'fields': ('tipo_alerta', 'prioridade', 'titulo', 'descricao')
        }),
        ('Produto', {
            'fields': ('produto', 'loja', 'lote', 'empresa')
        }),
        ('Quantidades', {
            'fields': ('quantidade_atual', 'quantidade_recomendada')
        }),
        ('Status', {
            'fields': ('ativo', 'data_resolucao', 'resolvido_por')
        }),
        ('Notificação', {
            'fields': ('notificado', 'data_notificacao')
        }),
        ('Resolução', {
            'fields': ('observacoes_resolucao',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['resolver_alertas', 'marcar_notificados']
    
    def resolver_alertas(self, request, queryset):
        count = 0
        for alerta in queryset.filter(ativo=True):
            alerta.resolver_alerta(request.user, "Resolvido em lote pelo admin")
            count += 1
        self.message_user(request, f'{count} alertas resolvidos.')
    resolver_alertas.short_description = 'Resolver alertas selecionados'
    
    def marcar_notificados(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(notificado=True, data_notificacao=timezone.now())
        self.message_user(request, f'{count} alertas marcados como notificados.')
    marcar_notificados.short_description = 'Marcar como notificados'

@admin.register(LocalizacaoEstoque)
class LocalizacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'created_at', 'updated_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativo']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Localização', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

