# apps/vendas/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.contrib import messages
from django.utils import timezone
from .models import (
     Comissao, DevolucaoVenda, HistoricoVenda, PagamentoVenda, Venda, ItemVenda
)
from .models import FormaPagamento



class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    readonly_fields = ['total']

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['numero_venda', 'empresa', 'cliente', 'tipo_venda', 'total', 'data_venda', 'status']
    list_filter = ['status', 'tipo_venda', 'empresa', 'loja', 'forma_pagamento']
    search_fields = ['numero_venda', 'cliente__nome']
    readonly_fields = ['numero_venda', 'data_venda', 'desconto_percentual', 'margem_lucro_total', 'quantidade_itens', 'troco', 'valor_pago', 'subtotal']
    
    inlines = [ItemVendaInline]
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('empresa', 'loja', 'numero_venda', 'data_venda', 'status', 'tipo_venda')
        }),
        ('Participantes', {
            'fields': ('cliente', 'vendedor', 'forma_pagamento')
        }),
        ('Valores', {
            'fields': ('subtotal', 'desconto_valor', 'desconto_percentual', 'total', 'valor_pago', 'troco', 'margem_lucro_total')
        }),
        ('Estatísticas', {
            'fields': ('quantidade_itens',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = ['venda', 'produto', 'quantidade', 'preco_unitario', 'total']
    list_filter = ['venda__empresa', 'venda__data_venda']
    search_fields = ['venda__numero_venda', 'produto__nome_comercial']

@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'tipo', 'permite_parcelamento', 'max_parcelas', 'ordem_exibicao',
        'taxa_administracao', 'necessita_tef', 'ativa'
    ]
    list_filter = ['tipo', 'permite_parcelamento', 'necessita_tef', 'ativa']
    search_fields = ['nome', 'codigo']
    list_editable = ['ativa', 'ordem_exibicao']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'codigo', 'tipo', 'empresa')
        }),
        ('Conta de Crédito', {
            'fields': ('conta_destino',),  # <-- aqui adiciona o campo
        }),
        ('Configurações', {
            'fields': ('requer_autorizacao', 'permite_parcelamento', 'max_parcelas', 'taxa_administracao')
        }),
        ('Integração', {
            'fields': ('codigo_integracao', 'necessita_tef')
        }),
        ('Validação', {
            'fields': ('valor_minimo', 'valor_maximo')
        }),
        ('Exibição', {
            'fields': ('ativa', 'ordem_exibicao')
        }),
    )



class PagamentoVendaInline(admin.TabularInline):
    model = PagamentoVenda
    extra = 0
    fields = [
        'forma_pagamento', 'valor_pago', 'numero_parcelas',
        'status', 'numero_autorizacao', 'nsu'
    ]
    readonly_fields = ['valor_taxa', 'valor_liquido']







@admin.register(PagamentoVenda)
class PagamentoVendaAdmin(admin.ModelAdmin):
    list_display = [
        'venda', 'forma_pagamento', 'valor_pago_display', 'numero_parcelas',
        'status_display', 'data_processamento', 'numero_autorizacao'
    ]
    list_filter = ['status', 'forma_pagamento', 'numero_parcelas', 'data_processamento']
    search_fields = [
        'venda__numero_venda', 'numero_autorizacao', 'nsu', 'tid'
    ]
    readonly_fields = ['valor_taxa', 'valor_liquido', 'valor_parcela']
    
    def valor_pago_display(self, obj):
        if obj.numero_parcelas > 1:
            return format_html(
                'R$ {:.2f}<br><small>{}x R$ {:.2f}</small>',
                obj.valor_pago, obj.numero_parcelas, obj.valor_parcela
            )
        return format_html('R$ {:.2f}', obj.valor_pago)
    valor_pago_display.short_description = 'Valor'
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'processando': 'blue',
            'aprovado': 'green',
            'rejeitado': 'red',
            'estornado': 'gray',
            'cancelado': 'red'
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(DevolucaoVenda)
class DevolucaoVendaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_devolucao', 'venda_original', 'motivo', 'valor_devolvido',
        'data_devolucao', 'aprovada', 'processada', 'solicitante'
    ]
    list_filter = ['motivo', 'aprovada', 'processada', 'data_devolucao']
    search_fields = ['numero_devolucao', 'venda_original__numero_venda', 'descricao_motivo']
    readonly_fields = ['numero_devolucao', 'data_devolucao']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_devolucao', 'venda_original', 'data_devolucao')
        }),
        ('Motivo', {
            'fields': ('motivo', 'descricao_motivo')
        }),
        ('Valores', {
            'fields': ('valor_devolvido', 'valor_restituido', 'taxa_devolucao')
        }),
        ('Responsáveis', {
            'fields': ('solicitante', 'aprovador')
        }),
        ('Status', {
            'fields': ('aprovada', 'processada')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    actions = ['aprovar_devolucoes', 'processar_devolucoes']
    
    def aprovar_devolucoes(self, request, queryset):
        count = queryset.update(aprovada=True, aprovador=request.user)
        messages.success(request, f'{count} devoluções aprovadas.')
    aprovar_devolucoes.short_description = "Aprovar devoluções selecionadas"
    
    def processar_devolucoes(self, request, queryset):
        count = queryset.filter(aprovada=True).update(processada=True)
        messages.success(request, f'{count} devoluções processadas.')
    processar_devolucoes.short_description = "Processar devoluções aprovadas"

@admin.register(HistoricoVenda)
class HistoricoVendaAdmin(admin.ModelAdmin):
    list_display = [
        'venda', 'status_anterior', 'status_novo', 'usuario', 'created_at'
    ]
    list_filter = ['status_anterior', 'status_novo', 'created_at', 'usuario']
    search_fields = ['venda__numero_venda', 'observacoes']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'venda', 
        'vendedor', 
        'valor_base', 
        'percentual', 
        'valor_comissao', 
        'status', 
        'data_pagamento', 
        'created_at'
    )
    list_filter = (
        'status', 
        'data_pagamento', 
        'created_at'
    )
    search_fields = (
        'venda__id', 
        'vendedor__username', 
        'vendedor__email'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_editable = ('status', 'data_pagamento')
    list_per_page = 25


# Adicionar ao arquivo apps/vendas/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    NotaCredito, ItemNotaCredito, NotaDebito, ItemNotaDebito,
    DocumentoTransporte, ItemDocumentoTransporte
)


class ItemNotaCreditoInline(admin.TabularInline):
    model = ItemNotaCredito
    extra = 0
    fields = (
        'produto', 'servico', 'descricao_item', 'quantidade_creditada',
        'valor_unitario_credito', 'iva_percentual', 'total_item_credito'
    )
    readonly_fields = ('total_item_credito',)


@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_nota', 'cliente', 'get_documento_origem', 'motivo', 
        'total', 'status', 'data_emissao', 'get_status_badge'
    )
    list_filter = (
        'status', 'data_nota', 'empresa', 'requer_aprovacao'
    )
    search_fields = (
        'numero_nota', 'cliente__nome_completo', 'cliente__nif',
        'venda_origem__numero_venda', 'fatura_credito_origem__numero_fatura'
    )
    readonly_fields = (
        'numero_nota', 'created_at', 'updated_at', 'data_aplicacao',
        'aprovada_por', 'data_aprovacao', 'aplicada_por'
    )
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_nota', 'empresa', 'status')
        }),
        ('Documento de Origem', {
            'fields': ('venda_origem', 'fatura_credito_origem')
        }),
        ('Dados do Cliente', {
            'fields': ('cliente', 'vendedor')
        }),
        ('Motivo e Descrição', {
            'fields': ('observacoes')
        }),
        ('Valores', {
            'fields': ('subtotal_credito', 'iva_credito', 'total')
        }),
        ('Aprovação', {
            'fields': ('requer_aprovacao', 'aprovada_por', 'data_aprovacao'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('emitida_por', 'data_emissao', 'aplicada_por', 'data_aplicacao', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ItemNotaCreditoInline]
    
    def get_documento_origem(self, obj):
        return obj.numero_documento_origem
    get_documento_origem.short_description = 'Documento Origem'
    
    def get_status_badge(self, obj):
        colors = {
            'rascunho': 'gray',
            'emitida': 'blue', 
            'aplicada': 'green',
            'cancelada': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'empresa'):
            qs = qs.filter(empresa=request.user.empresa)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.empresa = request.user.empresa
            obj.emitida_por = request.user
        super().save_model(request, obj, form, change)


class ItemNotaDebitoInline(admin.TabularInline):
    model = ItemNotaDebito
    extra = 0
    fields = (
        'produto', 'servico', 'descricao_item', 'quantidade',
        'valor_unitario', 'iva_percentual', 'total_item'
    )
    readonly_fields = ('total_item',)


@admin.register(NotaDebito)
class NotaDebitoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_nota', 'cliente', 'get_documento_origem', 
        'total', 'valor_pendente', 'status', 'data_vencimento', 'get_status_badge'
    )
    list_filter = (
        'status', 'data_nota', 'data_vencimento', 'empresa', 'requer_aprovacao'
    )
    search_fields = (
        'numero_nota', 'cliente__nome_completo', 'cliente__nif',
        'descricao_motivo', 'venda_origem__numero_venda', 
        'fatura_credito_origem__numero_fatura'
    )
    readonly_fields = (
        'numero_nota', 'created_at', 'updated_at', 'data_aplicacao',
        'aprovada_por', 'data_aprovacao', 'aplicada_por'
    )
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_nota', 'empresa', 'status')
        }),
        ('Documento de Origem', {
            'fields': ('venda_origem', 'fatura_credito_origem')
        }),
        ('Dados do Cliente', {
            'fields': ('cliente', 'vendedor')
        }),
        ('Motivo e Prazos', {
            'fields': ('motivo', 'descricao_motivo', 'data_vencimento', 'observacoes')
        }),
        ('Valores', {
            'fields': ('subtotal_debito', 'iva_debito', 'total', 'valor_pago')
        }),
        ('Aprovação', {
            'fields': ('requer_aprovacao', 'aprovada_por', 'data_aprovacao'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('emitida_por', 'data_emissao', 'aplicada_por', 'data_aplicacao', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ItemNotaDebitoInline]
    
    def get_documento_origem(self, obj):
        return obj.numero_documento_origem
    get_documento_origem.short_description = 'Documento Origem'
    
    def get_status_badge(self, obj):
        colors = {
            'rascunho': 'gray',
            'emitida': 'blue', 
            'aplicada': 'green',
            'cancelada': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'empresa'):
            qs = qs.filter(empresa=request.user.empresa)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.empresa = request.user.empresa
            obj.emitida_por = request.user
        super().save_model(request, obj, form, change)


class ItemDocumentoTransporteInline(admin.TabularInline):
    model = ItemDocumentoTransporte
    extra = 0
    fields = (
        'produto', 'codigo_produto', 'descricao_produto', 'quantidade_enviada',
        'peso_unitario', 'peso_total', 'valor_unitario', 'valor_total'
    )
    readonly_fields = ('peso_total', 'valor_total')


@admin.register(DocumentoTransporte)
class DocumentoTransporteAdmin(admin.ModelAdmin):
    list_display = (
        'numero_documento', 'destinatario_nome', 'get_documento_origem', 
        'tipo_operacao', 'status', 'data_inicio_transporte', 'data_previsao_entrega',
        'get_status_badge', 'get_atraso_badge'
    )
    list_filter = (
        'status', 'tipo_operacao', 'tipo_transporte', 'data_documento', 
        'destinatario_provincia', 'empresa'
    )
    search_fields = (
        'numero_documento', 'destinatario_nome', 'destinatario_nif',
        'transportador_nome', 'veiculo_matricula', 'condutor_nome',
        'venda_origem__numero_venda', 'fatura_credito_origem__numero_fatura'
    )
    readonly_fields = (
        'numero_documento', 'created_at', 'updated_at', 'data_entrega_real',
        'confirmado_entrega_por'
    )
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_documento', 'empresa', 'status', 'tipo_operacao', 'tipo_transporte')
        }),
        ('Documento de Origem', {
            'fields': ('venda_origem', 'fatura_credito_origem')
        }),
        ('Datas e Prazos', {
            'fields': ('data_documento', 'data_inicio_transporte', 'data_previsao_entrega', 'data_entrega_real')
        }),
        ('Remetente', {
            'fields': ('remetente_nome', 'remetente_nif', 'remetente_endereco', 'remetente_telefone', 'remetente_provincia'),
            'classes': ('collapse',)
        }),
        ('Destinatário', {
            'fields': ('destinatario_cliente', 'destinatario_nome', 'destinatario_nif', 'destinatario_endereco', 
                      'destinatario_telefone', 'destinatario_provincia')
        }),
        ('Transportador', {
            'fields': ('transportador_nome', 'transportador_nif', 'transportador_telefone')
        }),
        ('Veículo e Condutor', {
            'fields': ('veiculo_matricula', 'veiculo_modelo', 'condutor_nome', 'condutor_carta')
        }),
        ('Itinerário', {
            'fields': ('local_carregamento', 'local_descarga', 'itinerario')
        }),
        ('Valores e Medidas', {
            'fields': ('valor_transporte', 'peso_total', 'volume_total', 'quantidade_volumes')
        }),
        ('Observações', {
            'fields': ('observacoes', 'instrucoes_especiais')
        }),
        ('Assinaturas', {
            'fields': ('assinatura_remetente', 'assinatura_transportador', 'assinatura_destinatario'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('emitido_por', 'confirmado_entrega_por', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ItemDocumentoTransporteInline]
    
    def get_documento_origem(self, obj):
        return obj.numero_documento_origem
    get_documento_origem.short_description = 'Documento Origem'
    
    def get_status_badge(self, obj):
        colors = {
            'preparando': 'orange',
            'em_transito': 'blue',
            'entregue': 'green',
            'devolvido': 'purple',
            'cancelado': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_atraso_badge(self, obj):
        if obj.esta_atrasado and obj.status not in ['entregue', 'cancelado']:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ATRASADO</span>'
            )
        return ''
    get_atraso_badge.short_description = 'Atraso'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'empresa'):
            qs = qs.filter(empresa=request.user.empresa)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.empresa = request.user.empresa
            obj.emitido_por = request.user
        super().save_model(request, obj, form, change)


# Registrar os modelos de itens separadamente para acesso direto
@admin.register(ItemNotaCredito)
class ItemNotaCreditoAdmin(admin.ModelAdmin):
    list_display = (
        'nota_credito', 'descricao_item', 'quantidade_creditada', 
        'valor_unitario_credito', 'total_item_credito'
    )
    list_filter = ('nota_credito__empresa', 'produto')
    search_fields = ('descricao_item', 'nota_credito__numero_nota')


@admin.register(ItemNotaDebito)
class ItemNotaDebitoAdmin(admin.ModelAdmin):
    list_display = (
        'nota_debito', 'descricao_item', 'quantidade', 
        'valor_unitario', 'total_item'
    )
    list_filter = ('nota_debito__empresa', 'produto')
    search_fields = ('descricao_item', 'nota_debito__numero_nota')


@admin.register(ItemDocumentoTransporte)
class ItemDocumentoTransporteAdmin(admin.ModelAdmin):
    list_display = (
        'documento', 'codigo_produto', 'descricao_produto', 'quantidade_enviada',
        'quantidade_recebida', 'tem_divergencia', 'peso_total'
    )
    list_filter = ('documento__empresa', 'produto', 'tipo_embalagem')
    search_fields = ('codigo_produto', 'descricao_produto', 'documento__numero_documento')
    
    def tem_divergencia(self, obj):
        if obj.tem_divergencia:
            return format_html(
                '<span style="color: red; font-weight: bold;">SIM ({})</span>',
                obj.divergencia_quantidade
            )
        return 'NÃO'
    tem_divergencia.short_description = 'Divergência'


