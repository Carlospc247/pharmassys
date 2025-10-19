# apps/fornecedores/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.contrib import messages
from .models import (
    Fornecedor, ContatoFornecedor, CondicaoPagamento, 
    Pedido, ItemPedido, HistoricoPedido, AvaliacaoFornecedor
)

class ContatoFornecedorInline(admin.TabularInline):
    model = ContatoFornecedor
    extra = 1
    fields = ['nome', 'cargo', 'tipo_contato', 'telefone', 'email', 'contato_principal', 'ativo']

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_fornecedor', 'razao_social', 'categoria', 'cidade', 'provincia',
        'total_pedidos_display', 'total_display', 'nota_avaliacao', 'status_display'
    ]
    list_filter = [
        'categoria', 'provincia', 'ativo', 'bloqueado', 'tipo_pessoa',
         'permite_devolucao'
    ]
    search_fields = ['codigo_fornecedor', 'razao_social', 'nome_fantasia', 'nif_bi']
    readonly_fields = [
        'codigo_fornecedor', 'total_pedidos', 'total_comprado',
        'dias_sem_pedido', 'data_primeiro_pedido', 'data_ultimo_pedido'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'codigo_fornecedor', 'razao_social', 'nome_fantasia', 'tipo_pessoa', 'categoria', 'porte')
        }),
        ('Documentos', {
            'fields': ('nif_bi',)
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'bairro', 'cidade', 'provincia', 'postal', 'pais'),
            'classes': ['collapse']
        }),
        ('Contato', {
            'fields': ('telefone_principal', 'telefone_secundario', 'whatsapp', 'email_principal', 'email_financeiro', 'email_comercial', 'site'),
            'classes': ['collapse']
        }),
        ('Dados Comerciais', {
            'fields': ('condicao_pagamento_padrao', 'prazo_entrega_dias', 'valor_minimo_pedido')
        }),
        ('Dados Bancários', {
            'fields': ('banco_principal', 'agencia', 'conta_corrente'),
            'classes': ['collapse']
        }),
        ('Configurações Comerciais', {
            'fields': ('permite_devolucao', 'prazo_devolucao_dias', 'trabalha_consignacao', 'aceita_cartao', 'entrega_proprio'),
            'classes': ['collapse']
        }),
        ('Avaliação', {
            'fields': ('nota_avaliacao', 'pontualidade_entrega', 'qualidade_produtos')
        }),
        ('Status', {
            'fields': ('ativo', 'bloqueado', 'motivo_bloqueio')
        }),
        ('Histórico', {
            'fields': ('data_primeiro_pedido', 'data_ultimo_pedido', 'total_pedidos', 'total_comprado', 'dias_sem_pedido'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_internas'),
            'classes': ['collapse']
        }),
    )
    
    inlines = [ContatoFornecedorInline]
    actions = ['ativar_fornecedores', 'bloquear_fornecedores', 'desbloquear_fornecedores']
    
    def total_pedidos_display(self, obj):
        count = obj.total_pedidos
        if count > 0:
            url = reverse('admin:fornecedores_pedido_changelist') + f'?fornecedor__id__exact={obj.id}'
            return format_html('<a href="{}">{} pedidos</a>', url, count)
        return '0 pedidos'
    total_pedidos_display.short_description = 'Pedidos'
    
    def total_display(self, obj):
        valor = obj.total_comprado
        if valor > 0:
            return format_html('AKZ {:.2f}', valor)
        return 'AKZ 0,00'
    total_display.short_description = 'Total Comprado'
    
    def status_display(self, obj):
        if not obj.ativo:
            return format_html('<span style="color: red;">Inativo</span>')
        elif obj.bloqueado:
            return format_html('<span style="color: orange;">Bloqueado</span>')
        else:
            return format_html('<span style="color: green;">Ativo</span>')
    status_display.short_description = 'Status'
    
    def ativar_fornecedores(self, request, queryset):
        count = queryset.update(ativo=True)
        messages.success(request, f'{count} fornecedores ativados.')
    ativar_fornecedores.short_description = "Ativar fornecedores selecionados"
    
    def bloquear_fornecedores(self, request, queryset):
        count = queryset.update(bloqueado=True, motivo_bloqueio="Bloqueado via admin")
        messages.success(request, f'{count} fornecedores bloqueados.')
    bloquear_fornecedores.short_description = "Bloquear fornecedores selecionados"
    
    def desbloquear_fornecedores(self, request, queryset):
        count = queryset.update(bloqueado=False, motivo_bloqueio="")
        messages.success(request, f'{count} fornecedores desbloqueados.')
    desbloquear_fornecedores.short_description = "Desbloquear fornecedores selecionados"

@admin.register(CondicaoPagamento)
class CondicaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'prazo_dias', 'parcelas', 'desconto_a_vista', 'permite_cartao', 'ativa']
    list_filter = ['ativa', 'permite_cartao']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativa']


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = [
        'produto', 'quantidade', 'preco_unitario', 'desconto_item',
        'total', 'quantidade_recebida', 'saldo_pendente'
    ]
    readonly_fields = ['total', 'saldo_pendente']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_pedido', 'fornecedor', 'data_pedido', 'status_display',
        'urgencia_display', 'total_display', 'data_entrega_prevista',
        'percentual_recebido_display'
    ]
    list_filter = [
        'status', 'urgencia', 'data_pedido', 'fornecedor',
        'condicao_pagamento', 'data_entrega_prevista'
    ]
    search_fields = ['numero_pedido', 'fornecedor__razao_social', 'observacoes']
    readonly_fields = [
        'numero_pedido', 'subtotal', 'total', 'percentual_recebido',
        'dias_em_atraso', 'data_envio', 'data_confirmacao', 'data_aprovacao'
    ]
    date_hierarchy = 'data_pedido'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_pedido', 'fornecedor', 'status', 'urgencia')
        }),
        ('Datas', {
            'fields': ('data_pedido', 'data_envio', 'data_confirmacao', 'data_entrega_prevista', 'data_entrega_real')
        }),
        ('Valores', {
            'fields': ('subtotal', 'desconto_percentual', 'desconto_valor', 'valor_frete', 'valor_seguro', 'outras_despesas', 'total')
        }),
        ('Condições Comerciais', {
            'fields': ('condicao_pagamento', 'forma_pagamento')
        }),
        ('Entrega', {
            'fields': ('endereco_entrega', 'transportadora', 'numero_rastreamento'),
            'classes': ['collapse']
        }),
        ('Responsáveis', {
            'fields': ('solicitante', 'aprovador', 'data_aprovacao')
        }),
        ('Status', {
            'fields': ('percentual_recebido', 'dias_em_atraso')
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_internas', 'motivo_cancelamento'),
            'classes': ['collapse']
        }),
        ('Documentos', {
            'fields': ('arquivo_pedido', 'numero_orcamento_fornecedor'),
            'classes': ['collapse']
        }),
    )
    
    inlines = [ItemPedidoInline]
    actions = ['enviar_pedidos', 'cancelar_pedidos']
    
    def status_display(self, obj):
        color = obj.cor_status
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def urgencia_display(self, obj):
        colors = {'baixa': 'green', 'normal': 'blue', 'alta': 'orange', 'urgente': 'red'}
        color = colors.get(obj.urgencia, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_urgencia_display()
        )
    urgencia_display.short_description = 'Urgência'
    
    def total_display(self, obj):
        return format_html('R$ {:.2f}', obj.total)
    total_display.short_description = 'Valor Total'
    
    def percentual_recebido_display(self, obj):
        percentual = obj.percentual_recebido
        if percentual == 100:
            color = 'green'
        elif percentual > 0:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentual
        )
    percentual_recebido_display.short_description = '% Recebido'
    
    def enviar_pedidos(self, request, queryset):
        enviados = 0
        for pedido in queryset.filter(status='rascunho'):
            try:
                pedido.enviar_pedido(request.user)
                enviados += 1
            except Exception as e:
                messages.error(request, f'Erro ao enviar {pedido.numero_pedido}: {e}')
        
        if enviados:
            messages.success(request, f'{enviados} pedidos enviados.')
    enviar_pedidos.short_description = "Enviar pedidos selecionados"
    
    def cancelar_pedidos(self, request, queryset):
        cancelados = 0
        for pedido in queryset.exclude(status__in=['recebido', 'finalizado', 'cancelado']):
            pedido.cancelar_pedido(request.user, "Cancelado via admin")
            cancelados += 1
        
        if cancelados:
            messages.success(request, f'{cancelados} pedidos cancelados.')
    cancelar_pedidos.short_description = "Cancelar pedidos selecionados"


@admin.register(AvaliacaoFornecedor)
class AvaliacaoFornecedorAdmin(admin.ModelAdmin):
    list_display = [
        'fornecedor', 'pedido', 'nota_geral', 'nota_pontualidade',
        'nota_qualidade', 'recomendaria', 'avaliador', 'created_at'
    ]
    list_filter = ['recomendaria', 'created_at', 'nota_geral']
    search_fields = ['fornecedor__razao_social', 'pedido__numero_pedido']
    readonly_fields = ['nota_geral']
    
    fieldsets = (
        ('Avaliação', {
            'fields': ('fornecedor', 'pedido', 'avaliador')
        }),
        ('Notas', {
            'fields': ('nota_pontualidade', 'nota_qualidade', 'nota_atendimento', 'nota_preco', 'nota_geral')
        }),
        ('Comentários', {
            'fields': ('pontos_positivos', 'pontos_negativos', 'sugestoes')
        }),
        ('Recomendação', {
            'fields': ('recomendaria',)
        }),
    )

