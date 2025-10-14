# apps/financeiro/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.contrib import messages
from django.utils import timezone
from .models import (
    PlanoContas, CentroCusto, ContaBancaria, MovimentacaoFinanceira,
    ContaPagar, ContaReceber, FluxoCaixa, ConciliacaoBancaria, OrcamentoFinanceiro
)


def format_money(value, prefix="AKZ"):
    try:
        val = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0
    return f"{prefix} {val:,.2f}"



@admin.register(PlanoContas)
class PlanoContasAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo_conta', 'natureza', 'aceita_lancamento', 'ativa']
    list_filter = ['tipo_conta', 'natureza', 'aceita_lancamento', 'ativa']
    search_fields = ['codigo', 'nome', 'descricao']
    list_editable = ['ativa']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta_pai')

@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'responsavel', 'loja', 'ativo']
    list_filter = ['ativo', 'loja']
    search_fields = ['codigo', 'nome', 'descricao']
    list_editable = ['ativo']

@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'banco', 'agencia', 'conta', 'tipo_conta',
        'saldo_atual_display', 'saldo_disponivel_display', 'conta_principal', 'ativa'
    ]
    list_filter = ['tipo_conta', 'ativa', 'conta_principal']
    search_fields = ['nome', 'banco', 'agencia', 'conta']
    readonly_fields = ['saldo_atual', 'saldo_disponivel']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'banco', 'agencia', 'conta', 'digito', 'tipo_conta')
        }),
        ('Transferência', {
            'fields': ('kwik_chave', 'kwik_tipo'),
            'classes': ['collapse']
        }),
        ('Saldos', {
            'fields': ('saldo_inicial', 'saldo_atual', 'saldo_disponivel')
        }),
        ('Limites', {
            'fields': ('limite_credito', 'limite_kwik')
        }),
        ('Configurações', {
            'fields': ('ativa', 'conta_principal', 'permite_saldo_negativo')
        }),
        ('Integração', {
            'fields': ('codigo_integracao', 'ultima_conciliacao'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse']
        }),
    )
    
    actions = ['atualizar_saldos']
    
    def saldo_atual_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.saldo_atual))
    saldo_atual_display.short_description = "Saldo Atual"

    def saldo_disponivel_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.saldo_disponivel))
    saldo_disponivel_display.short_description = "Saldo Disponível"
    
    def atualizar_saldos(self, request, queryset):
        for conta in queryset:
            conta.atualizar_saldo()
        messages.success(request, f'Saldos atualizados para {queryset.count()} contas.')
    atualizar_saldos.short_description = "Atualizar saldos das contas"

@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimentacao', 'tipo_movimentacao_display', 'descricao',
        'valor_display', 'conta_bancaria', 'status_display', 'confirmada'
    ]
    list_filter = [
        'tipo_movimentacao', 'tipo_documento', 'status', 'confirmada',
        'conta_bancaria', 'data_movimentacao'
    ]
    search_fields = [
        'descricao', 'numero_documento', 'observacoes',
        'fornecedor__razao_social', 'cliente__nome_completo'
    ]
    readonly_fields = ['total']
    date_hierarchy = 'data_movimentacao'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_documento', 'tipo_movimentacao', 'tipo_documento', 'descricao')
        }),
        ('Datas', {
            'fields': ('data_movimentacao', 'data_vencimento', 'data_confirmacao')
        }),
        ('Valores', {
            'fields': ('valor', 'valor_juros', 'valor_multa', 'valor_desconto', 'total')
        }),
        ('Contas', {
            'fields': ('conta_bancaria', 'conta_destino', 'plano_contas', 'centro_custo')
        }),
        ('Relacionamentos', {
            'fields': ('fornecedor', 'cliente', 'venda_relacionada')
        }),
        ('Status', {
            'fields': ('status', 'confirmada', 'conciliada', 'data_conciliacao')
        }),
        ('Dados Específicos', {
            'fields': ('numero_cheque', 'banco_cheque', 'emissor_cheque', 'chave_kwik', 'txid_kwik'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse']
        }),
    )
    
    actions = ['confirmar_movimentacoes', 'cancelar_movimentacoes']
    
    def tipo_movimentacao_display(self, obj):
        colors = {'entrada': 'green', 'saida': 'red', 'transferencia': 'blue'}
        color = colors.get(obj.tipo_movimentacao, 'gray')
        icons = {'entrada': '↑', 'saida': '↓', 'transferencia': '↔'}
        icon = icons.get(obj.tipo_movimentacao, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_tipo_movimentacao_display()
        )
    tipo_movimentacao_display.short_description = 'Tipo'
    
    
    def valor_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor))
    valor_display.short_description = "Valor Atual"
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'confirmada': 'green',
            'cancelada': 'red',
            'estornada': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def confirmar_movimentacoes(self, request, queryset):
        confirmadas = 0
        for movimentacao in queryset.filter(status='pendente'):
            try:
                movimentacao.confirmar_movimentacao(request.user)
                confirmadas += 1
            except Exception as e:
                messages.error(request, f'Erro ao confirmar movimentação {movimentacao.id}: {e}')
        
        if confirmadas:
            messages.success(request, f'{confirmadas} movimentações confirmadas.')
    confirmar_movimentacoes.short_description = "Confirmar movimentações selecionadas"
    
    def cancelar_movimentacoes(self, request, queryset):
        canceladas = queryset.filter(status='pendente').update(status='cancelada')
        messages.success(request, f'{canceladas} movimentações canceladas.')
    cancelar_movimentacoes.short_description = "Cancelar movimentações selecionadas"


class ContaPagarInline(admin.TabularInline):
    model = ContaPagar
    fk_name = 'conta_pai'  # indica qual ForeignKey usar
    extra = 1

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento', 'descricao', 'fornecedor', 'data_vencimento',
        'valor_original_display', 'valor_saldo_display', 'status_display', 'dias_vencimento_display'
    ]
    list_filter = ['status', 'tipo_conta', 'data_vencimento', 'fornecedor']
    search_fields = ['numero_documento', 'descricao', 'fornecedor__razao_social']
    readonly_fields = ['valor_saldo', 'dias_vencimento', 'esta_vencida']
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_documento', 'descricao', 'tipo_conta')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_pagamento')
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_juros', 'valor_multa', 'valor_desconto', 'valor_pago', 'valor_saldo')
        }),
        ('Relacionamentos', {
            'fields': ('fornecedor', 'plano_contas', 'centro_custo')
        }),
        ('Parcelamento', {
            'fields': ('numero_parcela', 'total_parcelas', 'conta_pai'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('status', 'dias_vencimento', 'esta_vencida')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse']
        }),
    )
    
    actions = ['marcar_como_paga']
    
    def valor_original_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_original))
    valor_original_display.short_description = "Valor Original"
    
    def valor_saldo_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_saldo))
    valor_saldo_display.short_description = "Valor em Saldo"
    
    def status_display(self, obj):
        colors = {
            'aberta': 'blue',
            'vencida': 'red',
            'paga': 'green',
            'cancelada': 'gray',
            'renegociada': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} dias em atraso</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html('<span style="color: orange; font-weight: bold;">Vence hoje</span>')
        elif dias <= 7:
            return format_html(
                '<span style="color: orange;">Vence em {} dias</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">Vence em {} dias</span>', dias)
    dias_vencimento_display.short_description = 'Vencimento'
    
    def marcar_como_paga(self, request, queryset):
        count = 0
        for conta in queryset.filter(status__in=['aberta', 'vencida']):
            conta.valor_pago = conta.valor_original
            conta.save()
            count += 1
        
        messages.success(request, f'{count} contas marcadas como pagas.')
    marcar_como_paga.short_description = "Marcar como paga"


class ContaReceberInline(admin.TabularInline):
    model = ContaReceber
    fk_name = 'conta_pai'  # indica qual ForeignKey usar
    extra = 1

@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento', 'descricao', 'cliente', 'data_vencimento',
        'valor_original_display', 'valor_saldo_display', 'status_display', 'dias_vencimento_display'
    ]
    list_filter = ['status', 'tipo_conta', 'data_vencimento', 'cliente']
    search_fields = ['numero_documento', 'descricao', 'cliente__nome_completo']
    readonly_fields = ['valor_saldo', 'dias_vencimento_display', 'esta_vencida_display']
    date_hierarchy = 'data_vencimento'
    
    def valor_original_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_original))
    valor_original_display.short_description = "Valor Original"
    
    def valor_saldo_display(self, obj):
        if obj.valor_saldo > 0:
            color = 'red' if obj.esta_vencida else 'orange'
            return format_html(
                '<span style="color: {}; font-weight: bold;">AKZ {:.2f}</span>',
                color, obj.valor_saldo
            )
        return format_html('<span style="color: green;">R$ 0,00</span>')
    valor_saldo_display.short_description = 'Saldo'
    
    def status_display(self, obj):
        colors = {
            'aberta': 'blue',
            'vencida': 'red',
            'recebida': 'green',
            'cancelada': 'gray',
            'renegociada': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} dias em atraso</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html('<span style="color: orange; font-weight: bold;">Vence hoje</span>')
        elif dias <= 7:
            return format_html(
                '<span style="color: orange;">Vence em {} dias</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">Vence em {} dias</span>', dias)
    dias_vencimento_display.short_description = 'Vencimento'

    def esta_vencida_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'red' if obj.esta_vencida else 'green',
            'Sim' if obj.esta_vencida else 'Não'
        )
    esta_vencida_display.short_description = 'Está Vencida?'


@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    list_display = [
        'conta_bancaria', 'data_inicio', 'data_fim', 'saldo_banco_final',
        'saldo_sistema_final', 'diferenca_display', 'status_display'
    ]
    list_filter = ['status', 'conta_bancaria', 'data_fim']
    search_fields = ['conta_bancaria__nome', 'observacoes']
    
    def diferenca_display(self, obj):
        val = obj.diferenca or 0
        if abs(val) <= 0.01:
            return format_html('<span style="color: green;">{}</span>', format_money(0))
        return format_html('<span style="color: red; font-weight: bold;">{}</span>', format_money(val))
    diferenca_display.short_description = "Diferença"
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'conciliada': 'green',
            'divergente': 'red'
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

@admin.register(OrcamentoFinanceiro)
class OrcamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = [
        'ano', 'mes', 'plano_contas', 'tipo', 'valor_orcado_display',
        'valor_realizado_display', 'percentual_realizacao_display', 'variacao_display'
    ]
    list_filter = ['ano', 'mes', 'tipo', 'plano_contas']
    search_fields = ['plano_contas__nome']
    readonly_fields = ['valor_variacao', 'percentual_realizacao']
    
    actions = ['atualizar_realizados']
    
    def valor_orcado_display(self, obj):
        return format_html('AKZ {:.2f}', obj.valor_orcado)
    valor_orcado_display.short_description = 'Orçado'
    
    def valor_realizado_display(self, obj):
        return format_html('AKZ {:.2f}', obj.valor_realizado)
    valor_realizado_display.short_description = 'Realizado'
    
    def percentual_realizacao_display(self, obj):
        if obj.percentual_realizacao > 100:
            color = 'red'
        elif obj.percentual_realizacao >= 90:
            color = 'green'
        elif obj.percentual_realizacao >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.percentual_realizacao
        )
    percentual_realizacao_display.short_description = '% Realizado'
    
    def variacao_display(self, obj):
        val = obj.variacao or 0
        color = "green" if val >= 0 else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, round(val, 2))
    variacao_display.short_description = "Variação (%)"
    
    def atualizar_realizados(self, request, queryset):
        for orcamento in queryset:
            orcamento.atualizar_realizado()
        
        messages.success(request, f'Valores realizados atualizados para {queryset.count()} orçamentos.')
    atualizar_realizados.short_description = "Atualizar valores realizados"

