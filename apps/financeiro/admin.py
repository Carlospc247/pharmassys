from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, datetime, timedelta
from .models import (
    PlanoContas, CentroCusto, ContaBancaria, MovimentacaoFinanceira,
    ContaPagar, ContaReceber, FluxoCaixa, ConciliacaoBancaria, 
    OrcamentoFinanceiro, CategoriaFinanceira, LancamentoFinanceiro,
    MovimentoCaixa, ImpostoTributo, ConfiguracaoImposto
)

def format_money(value, prefix="AKZ"):
    """Formatar valor monetário"""
    try:
        val = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0
    return f"{prefix} {val:,.2f}"

def format_percentage(value):
    """Formatar percentual"""
    try:
        val = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0
    return f"{val:.2f}%"

# =====================================
# PLANO DE CONTAS
# =====================================

class ContasFilhasInline(admin.TabularInline):
    model = PlanoContas
    fk_name = 'conta_pai'
    extra = 0
    fields = ['codigo', 'nome', 'tipo_conta', 'natureza', 'aceita_lancamento', 'ativa']
    readonly_fields = []

@admin.register(PlanoContas)
class PlanoContasAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'tipo_conta_display', 'natureza_display', 
        'conta_pai', 'nivel', 'aceita_lancamento', 'ativa', 'ordem'
    ]
    list_filter = ['tipo_conta', 'natureza', 'aceita_lancamento', 'ativa', 'nivel']
    search_fields = ['codigo', 'nome', 'descricao']
    list_editable = ['ativa', 'aceita_lancamento', 'ordem']
    ordering = ['codigo']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao')
        }),
        ('Hierarquia', {
            'fields': ('conta_pai', 'nivel')
        }),
        ('Características', {
            'fields': ('tipo_conta', 'natureza', 'aceita_lancamento')
        }),
        ('Configurações', {
            'fields': ('ativa', 'ordem')
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    inlines = [ContasFilhasInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta_pai', 'empresa')
    
    def tipo_conta_display(self, obj):
        colors = {
            'receita': 'green',
            'despesa': 'red',
            'ativo': 'blue',
            'passivo': 'orange',
            'patrimonio': 'purple'
        }
        color = colors.get(obj.tipo_conta, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_tipo_conta_display()
        )
    tipo_conta_display.short_description = 'Tipo'
    
    def natureza_display(self, obj):
        colors = {'debito': 'red', 'credito': 'green'}
        color = colors.get(obj.natureza, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_natureza_display()
        )
    natureza_display.short_description = 'Natureza'

# =====================================
# CENTRO DE CUSTO
# =====================================

@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'responsavel', 'loja', 'ativo', 'empresa'
    ]
    list_filter = ['ativo', 'loja', 'empresa']
    search_fields = ['codigo', 'nome', 'descricao', 'responsavel__nome']
    list_editable = ['ativo']
    ordering = ['codigo']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao')
        }),
        ('Responsabilidade', {
            'fields': ('responsavel', 'loja')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('responsavel', 'loja', 'empresa')

# =====================================
# CONTA BANCÁRIA
# =====================================

@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'banco', 'agencia_conta', 'tipo_conta_display',
        'saldo_atual_display', 'saldo_disponivel_display', 
        'conta_principal', 'ativa'
    ]
    list_filter = ['tipo_conta', 'ativa', 'conta_principal', 'banco']
    search_fields = ['nome', 'banco', 'agencia', 'conta', 'kwik_chave']
    readonly_fields = ['saldo_atual', 'saldo_disponivel']
    list_editable = ['ativa']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'banco', 'agencia', 'conta', 'digito', 'tipo_conta')
        }),
        ('Transferência Eletrônica', {
            'fields': ('kwik_chave', 'kwik_tipo'),
            'classes': ['collapse']
        }),
        ('Saldos e Limites', {
            'fields': ('saldo_inicial', 'saldo_atual', 'limite_credito', 'limite_kwik')
        }),
        ('Configurações', {
            'fields': ('ativa', 'conta_principal', 'permite_saldo_negativo')
        }),
        ('Integração', {
            'fields': ('codigo_integracao', 'ultima_conciliacao', 'plano_contas_ativo'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse']
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['atualizar_saldos', 'marcar_como_principal']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('empresa', 'plano_contas_ativo')
    
    def agencia_conta(self, obj):
        return f"Ag: {obj.agencia} | Cc: {obj.conta}"
    agencia_conta.short_description = "Agência/Conta"
    
    def tipo_conta_display(self, obj):
        icons = {
            'corrente': '💳',
            'poupanca': '🏦',
            'investimento': '📈',
            'cartao': '💸',
            'caixa': '💰'
        }
        icon = icons.get(obj.tipo_conta, '💰')
        return format_html(
            '{} {}', icon, obj.get_tipo_conta_display()
        )
    tipo_conta_display.short_description = "Tipo"
    
    def saldo_atual_display(self, obj):
        color = 'green' if obj.saldo_atual >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(obj.saldo_atual)
        )
    saldo_atual_display.short_description = "Saldo Atual"

    def saldo_disponivel_display(self, obj):
        saldo = obj.saldo_disponivel
        color = 'green' if saldo >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(saldo)
        )
    saldo_disponivel_display.short_description = "Saldo Disponível"
    
    def atualizar_saldos(self, request, queryset):
        count = 0
        for conta in queryset:
            conta.atualizar_saldo()
            count += 1
        messages.success(request, f'Saldos atualizados para {count} contas.')
    atualizar_saldos.short_description = "Atualizar saldos das contas"
    
    def marcar_como_principal(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, 'Selecione apenas uma conta para marcar como principal.')
            return
        
        conta = queryset.first()
        # Desmarcar outras contas principais da mesma empresa
        ContaBancaria.objects.filter(empresa=conta.empresa, conta_principal=True).update(conta_principal=False)
        conta.conta_principal = True
        conta.save()
        messages.success(request, f'Conta {conta.nome} marcada como principal.')
    marcar_como_principal.short_description = "Marcar como conta principal"

# =====================================
# MOVIMENTAÇÃO FINANCEIRA
# =====================================

@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimentacao', 'tipo_movimentacao_display', 'descricao_truncada',
        'valor_display', 'conta_bancaria', 'status_display', 'confirmada'
    ]
    list_filter = [
        'tipo_movimentacao', 'tipo_documento', 'status', 'confirmada',
        'conta_bancaria', 'data_movimentacao', 'plano_contas__tipo_conta'
    ]
    search_fields = [
        'descricao', 'numero_documento', 'observacoes',
        'fornecedor__razao_social', 'cliente__nome_completo'
    ]
    readonly_fields = ['total']
    date_hierarchy = 'data_movimentacao'
    ordering = ['-data_movimentacao', '-created_at']
    
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
            'fields': ('fornecedor', 'cliente', 'venda_relacionada', 'recibo')
        }),
        ('Status e Controle', {
            'fields': ('status', 'confirmada', 'conciliada', 'data_conciliacao', 'usuario_responsavel')
        }),
        ('Dados Específicos', {
            'fields': ('numero_cheque', 'banco_cheque', 'emissor_cheque', 'chave_kwik', 'txid_kwik'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ['collapse']
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['confirmar_movimentacoes', 'cancelar_movimentacoes', 'conciliar_movimentacoes']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conta_bancaria', 'plano_contas', 'fornecedor', 'cliente', 'usuario_responsavel'
        )
    
    def descricao_truncada(self, obj):
        if len(obj.descricao) > 50:
            return obj.descricao[:50] + '...'
        return obj.descricao
    descricao_truncada.short_description = "Descrição"
    
    def tipo_movimentacao_display(self, obj):
        colors = {'entrada': 'green', 'saida': 'red', 'transferencia': 'blue'}
        icons = {'entrada': '⬆️', 'saida': '⬇️', 'transferencia': '↔️'}
        color = colors.get(obj.tipo_movimentacao, 'gray')
        icon = icons.get(obj.tipo_movimentacao, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_tipo_movimentacao_display()
        )
    tipo_movimentacao_display.short_description = 'Tipo'
    
    def valor_display(self, obj):
        color = 'green' if obj.tipo_movimentacao == 'entrada' else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(obj.valor)
        )
    valor_display.short_description = "Valor"
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'confirmada': 'green',
            'cancelada': 'red',
            'estornada': 'gray'
        }
        icons = {
            'pendente': '⏳',
            'confirmada': '✅',
            'cancelada': '❌',
            'estornada': '🔄'
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
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
    
    def conciliar_movimentacoes(self, request, queryset):
        conciliadas = queryset.filter(confirmada=True, conciliada=False).update(
            conciliada=True, 
            data_conciliacao=date.today()
        )
        messages.success(request, f'{conciliadas} movimentações conciliadas.')
    conciliar_movimentacoes.short_description = "Marcar como conciliadas"

# =====================================
# CONTA A PAGAR
# =====================================

class ParcelasContaPagarInline(admin.TabularInline):
    model = ContaPagar
    fk_name = 'conta_pai'
    extra = 0
    fields = ['numero_parcela', 'data_vencimento', 'valor_original', 'valor_pago', 'status']
    readonly_fields = ['valor_saldo']

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento', 'descricao_truncada', 'fornecedor', 'data_vencimento',
        'valor_original_display', 'valor_saldo_display', 'status_display', 'dias_vencimento_display'
    ]
    list_filter = ['status', 'tipo_conta', 'data_vencimento', 'fornecedor', 'data_emissao']
    search_fields = ['numero_documento', 'descricao', 'fornecedor__razao_social']
    readonly_fields = ['valor_saldo', 'dias_vencimento', 'esta_vencida']
    date_hierarchy = 'data_vencimento'
    ordering = ['data_vencimento', 'valor_saldo']
    
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
        ('Status e Observações', {
            'fields': ('status', 'dias_vencimento', 'esta_vencida', 'observacoes')
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    inlines = [ParcelasContaPagarInline]
    actions = ['marcar_como_paga', 'gerar_relatorio_vencimentos']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fornecedor', 'plano_contas', 'empresa')
    
    def descricao_truncada(self, obj):
        if len(obj.descricao) > 40:
            return obj.descricao[:40] + '...'
        return obj.descricao
    descricao_truncada.short_description = "Descrição"
    
    def valor_original_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_original))
    valor_original_display.short_description = "Valor Original"
    
    def valor_saldo_display(self, obj):
        if obj.valor_saldo > 0:
            color = 'red' if obj.esta_vencida else 'orange'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, format_money(obj.valor_saldo)
            )
        return format_html('<span style="color: green;">AKZ 0,00</span>')
    valor_saldo_display.short_description = "Saldo"
    
    def status_display(self, obj):
        colors = {
            'aberta': 'blue',
            'vencida': 'red',
            'paga': 'green',
            'cancelada': 'gray',
            'renegociada': 'orange'
        }
        icons = {
            'aberta': '📋',
            'vencida': '⚠️',
            'paga': '✅',
            'cancelada': '❌',
            'renegociada': '🔄'
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} dias em atraso</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html('<span style="color: orange; font-weight: bold;">🕐 Vence hoje</span>')
        elif dias <= 7:
            return format_html(
                '<span style="color: orange;">⏰ Vence em {} dias</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">📅 Vence em {} dias</span>', dias)
    dias_vencimento_display.short_description = 'Vencimento'
    
    def marcar_como_paga(self, request, queryset):
        count = 0
        for conta in queryset.filter(status__in=['aberta', 'vencida']):
            conta.valor_pago = conta.valor_original + conta.valor_juros + conta.valor_multa - conta.valor_desconto
            conta.save()
            count += 1
        
        messages.success(request, f'{count} contas marcadas como pagas.')
    marcar_como_paga.short_description = "Marcar como paga"
    
    def gerar_relatorio_vencimentos(self, request, queryset):
        total_vencidas = queryset.filter(status='vencida').count()
        total_valor_vencido = queryset.filter(status='vencida').aggregate(
            total=Sum('valor_saldo')
        )['total'] or 0
        
        messages.info(
            request, 
            f'Relatório: {total_vencidas} contas vencidas totalizando {format_money(total_valor_vencido)}'
        )
    gerar_relatorio_vencimentos.short_description = "Gerar relatório de vencimentos"

# =====================================
# CONTA A RECEBER
# =====================================

class ParcelasContaReceberInline(admin.TabularInline):
    model = ContaReceber
    fk_name = 'conta_pai'
    extra = 0
    fields = ['numero_parcela', 'data_vencimento', 'valor_original', 'valor_recebido', 'status']
    readonly_fields = ['valor_saldo']

@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento', 'descricao_truncada', 'cliente', 'data_vencimento',
        'valor_original_display', 'valor_saldo_display', 'status_display', 'dias_vencimento_display'
    ]
    list_filter = ['status', 'tipo_conta', 'data_vencimento', 'cliente', 'data_emissao']
    search_fields = ['numero_documento', 'descricao', 'cliente__nome_completo']
    readonly_fields = ['valor_saldo', 'dias_vencimento', 'esta_vencida']
    date_hierarchy = 'data_vencimento'
    ordering = ['data_vencimento', 'valor_saldo']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_documento', 'descricao', 'tipo_conta')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_recebimento')
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_juros', 'valor_multa', 'valor_desconto', 'valor_recebido', 'valor_saldo')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'venda', 'plano_contas', 'centro_custo')
        }),
        ('Parcelamento', {
            'fields': ('numero_parcela', 'total_parcelas', 'conta_pai'),
            'classes': ['collapse']
        }),
        ('Status e Observações', {
            'fields': ('status', 'dias_vencimento', 'esta_vencida', 'observacoes')
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    inlines = [ParcelasContaReceberInline]
    actions = ['marcar_como_recebida', 'aplicar_desconto', 'gerar_cobranca']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'venda', 'plano_contas', 'empresa')
    
    def descricao_truncada(self, obj):
        if len(obj.descricao) > 40:
            return obj.descricao[:40] + '...'
        return obj.descricao
    descricao_truncada.short_description = "Descrição"
    
    def valor_original_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_original))
    valor_original_display.short_description = "Valor Original"
    
    def valor_saldo_display(self, obj):
        if obj.valor_saldo > 0:
            color = 'red' if obj.esta_vencida else 'orange'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, format_money(obj.valor_saldo)
            )
        return format_html('<span style="color: green;">AKZ 0,00</span>')
    valor_saldo_display.short_description = 'Saldo'
    
    def status_display(self, obj):
        colors = {
            'aberta': 'blue',
            'vencida': 'red',
            'recebida': 'green',
            'cancelada': 'gray',
            'renegociada': 'orange'
        }
        icons = {
            'aberta': '📋',
            'vencida': '⚠️',
            'recebida': '✅',
            'cancelada': '❌',
            'renegociada': '🔄'
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} dias em atraso</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html('<span style="color: orange; font-weight: bold;">🕐 Vence hoje</span>')
        elif dias <= 7:
            return format_html(
                '<span style="color: orange;">⏰ Vence em {} dias</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">📅 Vence em {} dias</span>', dias)
    dias_vencimento_display.short_description = 'Vencimento'
    
    def marcar_como_recebida(self, request, queryset):
        count = 0
        for conta in queryset.filter(status__in=['aberta', 'vencida']):
            conta.valor_recebido = conta.valor_original + conta.valor_juros + conta.valor_multa - conta.valor_desconto
            conta.save()
            count += 1
        
        messages.success(request, f'{count} contas marcadas como recebidas.')
    marcar_como_recebida.short_description = "Marcar como recebida"
    
    def aplicar_desconto(self, request, queryset):
        # Simular aplicação de desconto de 5%
        count = 0
        for conta in queryset.filter(status__in=['aberta', 'vencida']):
            if conta.valor_desconto == 0:
                conta.valor_desconto = conta.valor_original * Decimal('0.05')
                conta.save()
                count += 1
        
        messages.success(request, f'Desconto de 5% aplicado a {count} contas.')
    aplicar_desconto.short_description = "Aplicar desconto de 5%"
    
    def gerar_cobranca(self, request, queryset):
        total_cobrancas = queryset.filter(status__in=['aberta', 'vencida']).count()
        total_valor = queryset.filter(status__in=['aberta', 'vencida']).aggregate(
            total=Sum('valor_saldo')
        )['total'] or 0
        
        messages.info(
            request, 
            f'Cobrança gerada: {total_cobrancas} contas totalizando {format_money(total_valor)}'
        )
    gerar_cobranca.short_description = "Gerar cobrança"

# =====================================
# FLUXO DE CAIXA
# =====================================

@admin.register(FluxoCaixa)
class FluxoCaixaAdmin(admin.ModelAdmin):
    list_display = [
        'data_referencia', 'tipo_display', 'categoria', 'descricao_truncada',
        'valor_previsto_display', 'valor_realizado_display', 'saldo_acumulado_display', 'realizado'
    ]
    list_filter = ['tipo', 'realizado', 'categoria', 'conta_bancaria', 'data_referencia']
    search_fields = ['categoria', 'descricao', 'observacoes']
    date_hierarchy = 'data_referencia'
    ordering = ['data_referencia']
    
    fieldsets = (
        ('Data e Tipo', {
            'fields': ('data_referencia', 'tipo')
        }),
        ('Valores', {
            'fields': ('valor_previsto', 'valor_realizado', 'saldo_acumulado')
        }),
        ('Classificação', {
            'fields': ('categoria', 'descricao')
        }),
        ('Relacionamentos', {
            'fields': ('conta_bancaria', 'centro_custo', 'conta_pagar', 'conta_receber')
        }),
        ('Status', {
            'fields': ('realizado', 'observacoes')
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['marcar_como_realizado', 'calcular_projecoes']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta_bancaria', 'centro_custo', 'empresa')
    
    def descricao_truncada(self, obj):
        if len(obj.descricao) > 40:
            return obj.descricao[:40] + '...'
        return obj.descricao
    descricao_truncada.short_description = "Descrição"
    
    def tipo_display(self, obj):
        colors = {'entrada': 'green', 'saida': 'red'}
        icons = {'entrada': '⬆️', 'saida': '⬇️'}
        color = colors.get(obj.tipo, 'gray')
        icon = icons.get(obj.tipo, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_tipo_display()
        )
    tipo_display.short_description = 'Tipo'
    
    def valor_previsto_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_previsto))
    valor_previsto_display.short_description = "Previsto"
    
    def valor_realizado_display(self, obj):
        color = 'green' if obj.valor_realizado > 0 else 'gray'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, format_money(obj.valor_realizado)
        )
    valor_realizado_display.short_description = "Realizado"
    
    def saldo_acumulado_display(self, obj):
        color = 'green' if obj.saldo_acumulado >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(obj.saldo_acumulado)
        )
    saldo_acumulado_display.short_description = "Saldo Acumulado"
    
    def marcar_como_realizado(self, request, queryset):
        count = queryset.filter(realizado=False).update(realizado=True)
        messages.success(request, f'{count} itens marcados como realizados.')
    marcar_como_realizado.short_description = "Marcar como realizado"
    
    def calcular_projecoes(self, request, queryset):
        messages.info(request, f'Cálculo de projeções executado para {queryset.count()} itens.')
    calcular_projecoes.short_description = "Calcular projeções"

# =====================================
# CONCILIAÇÃO BANCÁRIA
# =====================================

@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    list_display = [
        'conta_bancaria', 'periodo_display', 'saldo_banco_final_display',
        'saldo_sistema_final_display', 'diferenca_display', 'status_display'
    ]
    list_filter = ['status', 'conta_bancaria', 'data_fim']
    search_fields = ['conta_bancaria__nome', 'observacoes']
    date_hierarchy = 'data_fim'
    ordering = ['-data_fim']
    
    fieldsets = (
        ('Conta e Período', {
            'fields': ('conta_bancaria', 'data_inicio', 'data_fim')
        }),
        ('Saldos Bancários', {
            'fields': ('saldo_banco_inicial', 'saldo_banco_final')
        }),
        ('Saldos do Sistema', {
            'fields': ('saldo_sistema_inicial', 'saldo_sistema_final')
        }),
        ('Resultado', {
            'fields': ('diferenca', 'status', 'data_conciliacao')
        }),
        ('Responsável', {
            'fields': ('responsavel',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    readonly_fields = ['diferenca']
    actions = ['recalcular_diferencas']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta_bancaria', 'responsavel')
    
    def periodo_display(self, obj):
        return f"{obj.data_inicio.strftime('%d/%m')} a {obj.data_fim.strftime('%d/%m/%Y')}"
    periodo_display.short_description = "Período"
    
    def saldo_banco_final_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.saldo_banco_final))
    saldo_banco_final_display.short_description = "Saldo Banco"
    
    def saldo_sistema_final_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.saldo_sistema_final))
    saldo_sistema_final_display.short_description = "Saldo Sistema"
    
    def diferenca_display(self, obj):
        val = obj.diferenca or 0
        if abs(val) <= 0.01:
            return format_html('<span style="color: green;">✅ {}</span>', format_money(0))
        color = 'red' if val != 0 else 'green'
        return format_html('<span style="color: {}; font-weight: bold;">⚠️ {}</span>', color, format_money(val))
    diferenca_display.short_description = "Diferença"
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'conciliada': 'green',
            'divergente': 'red'
        }
        icons = {
            'pendente': '⏳',
            'conciliada': '✅',
            'divergente': '⚠️'
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def recalcular_diferencas(self, request, queryset):
        for conciliacao in queryset:
            conciliacao.save()  # Vai recalcular a diferença
        messages.success(request, f'Diferenças recalculadas para {queryset.count()} conciliações.')
    recalcular_diferencas.short_description = "Recalcular diferenças"

# =====================================
# ORÇAMENTO FINANCEIRO
# =====================================

@admin.register(OrcamentoFinanceiro)
class OrcamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = [
        'periodo_display', 'plano_contas', 'tipo_display', 'valor_orcado_display',
        'valor_realizado_display', 'percentual_realizacao_display', 'variacao_display'
    ]
    list_filter = ['ano', 'mes', 'tipo', 'plano_contas__tipo_conta']
    search_fields = ['plano_contas__nome', 'justificativa_variacao']
    readonly_fields = ['valor_variacao', 'percentual_realizacao']
    ordering = ['-ano', '-mes']
    
    fieldsets = (
        ('Período', {
            'fields': ('ano', 'mes')
        }),
        ('Classificação', {
            'fields': ('tipo', 'plano_contas', 'centro_custo')
        }),
        ('Valores', {
            'fields': ('valor_orcado', 'valor_realizado', 'valor_variacao', 'percentual_realizacao')
        }),
        ('Justificativa', {
            'fields': ('justificativa_variacao',)
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['atualizar_realizados', 'gerar_relatorio_variacao']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('plano_contas', 'centro_custo', 'empresa')
    
    def periodo_display(self, obj):
        return f"{obj.mes:02d}/{obj.ano}"
    periodo_display.short_description = "Período"
    
    def tipo_display(self, obj):
        colors = {'receita': 'green', 'despesa': 'red'}
        color = colors.get(obj.tipo, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_display.short_description = 'Tipo'
    
    def valor_orcado_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_orcado))
    valor_orcado_display.short_description = 'Orçado'
    
    def valor_realizado_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_realizado))
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
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_percentage(obj.percentual_realizacao)
        )
    percentual_realizacao_display.short_description = '% Realizado'
    
    def variacao_display(self, obj):
        val = obj.valor_variacao or 0
        color = "green" if val >= 0 else "red"
        icon = "📈" if val >= 0 else "📉"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, format_money(abs(val))
        )
    variacao_display.short_description = "Variação"
    
    def atualizar_realizados(self, request, queryset):
        for orcamento in queryset:
            orcamento.atualizar_realizado()
        
        messages.success(request, f'Valores realizados atualizados para {queryset.count()} orçamentos.')
    atualizar_realizados.short_description = "Atualizar valores realizados"
    
    def gerar_relatorio_variacao(self, request, queryset):
        total_variacao = queryset.aggregate(total=Sum('valor_variacao'))['total'] or 0
        messages.info(request, f'Variação total: {format_money(total_variacao)}')
    gerar_relatorio_variacao.short_description = "Gerar relatório de variação"

# =====================================
# CATEGORIA FINANCEIRA
# =====================================

@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_dre_display', 'descricao_truncada']
    list_filter = ['tipo_dre']
    search_fields = ['nome', 'descricao']
    ordering = ['tipo_dre', 'nome']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'descricao')
        }),
        ('Classificação DRE', {
            'fields': ('tipo_dre',)
        }),
    )
    
    def descricao_truncada(self, obj):
        if obj.descricao and len(obj.descricao) > 50:
            return obj.descricao[:50] + '...'
        return obj.descricao or '-'
    descricao_truncada.short_description = "Descrição"
    
    def tipo_dre_display(self, obj):
        colors = {
            'receita': 'green',
            'deducao': 'orange',
            'custo': 'red',
            'despesa': 'red',
            'financeiro': 'blue',
            'outros': 'gray'
        }
        color = colors.get(obj.tipo_dre, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_tipo_dre_display()
        )
    tipo_dre_display.short_description = 'Tipo DRE'

# =====================================
# LANÇAMENTO FINANCEIRO
# =====================================

@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = [
        'numero_lancamento', 'data_lancamento', 'tipo_display', 
        'valor_display', 'plano_contas', 'descricao_truncada'
    ]
    list_filter = ['tipo', 'data_lancamento', 'plano_contas__tipo_conta']
    search_fields = ['numero_lancamento', 'descricao', 'plano_contas__nome']
    date_hierarchy = 'data_lancamento'
    ordering = ['-data_lancamento', 'numero_lancamento']
    readonly_fields = ['transacao_uuid']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_lancamento', 'data_lancamento', 'descricao')
        }),
        ('Valores', {
            'fields': ('tipo', 'valor')
        }),
        ('Contas', {
            'fields': ('plano_contas', 'centro_custo')
        }),
        ('Rastreamento', {
            'fields': ('origem_movimentacao', 'transacao_uuid')
        }),
        ('Responsável', {
            'fields': ('usuario_responsavel',)
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['gerar_balancete']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'plano_contas', 'centro_custo', 'usuario_responsavel', 'origem_movimentacao'
        )
    
    def descricao_truncada(self, obj):
        if len(obj.descricao) > 40:
            return obj.descricao[:40] + '...'
        return obj.descricao
    descricao_truncada.short_description = "Descrição"
    
    def tipo_display(self, obj):
        colors = {'debito': 'red', 'credito': 'green'}
        icons = {'debito': '📤', 'credito': '📥'}
        color = colors.get(obj.tipo, 'gray')
        icon = icons.get(obj.tipo, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_tipo_display().upper()
        )
    tipo_display.short_description = 'Tipo'
    
    def valor_display(self, obj):
        color = 'red' if obj.tipo == 'debito' else 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(obj.valor)
        )
    valor_display.short_description = "Valor"
    
    def gerar_balancete(self, request, queryset):
        total_debitos = queryset.filter(tipo='debito').aggregate(total=Sum('valor'))['total'] or 0
        total_creditos = queryset.filter(tipo='credito').aggregate(total=Sum('valor'))['total'] or 0
        
        messages.info(
            request, 
            f'Balancete: Débitos {format_money(total_debitos)} | Créditos {format_money(total_creditos)}'
        )
    gerar_balancete.short_description = "Gerar balancete"

# =====================================
# MOVIMENTO DE CAIXA
# =====================================

@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_movimento', 'data_movimento', 'tipo_movimento_display', 
        'valor_display', 'forma_pagamento_display', 'status_display', 'loja'
    ]
    list_filter = ['tipo_movimento', 'forma_pagamento', 'status', 'loja', 'data_movimento']
    search_fields = ['numero_movimento', 'descricao', 'observacoes']
    date_hierarchy = 'data_movimento'
    ordering = ['-data_movimento', '-hora_movimento']
    readonly_fields = ['numero_movimento', 'valor_liquido']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_movimento', 'data_movimento', 'hora_movimento')
        }),
        ('Tipo e Forma', {
            'fields': ('tipo_movimento', 'forma_pagamento')
        }),
        ('Valores', {
            'fields': ('valor', 'valor_troco', 'valor_liquido')
        }),
        ('Descrição', {
            'fields': ('descricao', 'observacoes')
        }),
        ('Relacionamentos', {
            'fields': ('usuario', 'loja', 'venda_relacionada')
        }),
        ('Contas Financeiras', {
            'fields': ('conta_receber', 'conta_pagar', 'cliente', 'fornecedor'),
            'classes': ['collapse']
        }),
        ('Status e Controle', {
            'fields': ('status', 'confirmado', 'data_confirmacao')
        }),
        ('Dados do Documento', {
            'fields': ('numero_documento',),
            'classes': ['collapse']
        }),
        ('Dados do Cheque', {
            'fields': ('numero_cheque', 'banco_cheque', 'emissor_cheque', 'data_cheque'),
            'classes': ['collapse']
        }),
        ('Dados KWIK', {
            'fields': ('chave_kwik', 'txid_kwik'),
            'classes': ['collapse']
        }),
        ('Dados do Cartão', {
            'fields': ('numero_cartao_mascarado', 'bandeira_cartao', 'numero_autorizacao', 'numero_comprovante'),
            'classes': ['collapse']
        }),
        ('Estorno', {
            'fields': ('movimento_original',),
            'classes': ['collapse']
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['confirmar_movimentos', 'estornar_movimentos', 'gerar_fechamento_caixa']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'usuario', 'loja', 'venda_relacionada', 'cliente', 'fornecedor'
        )
    
    def tipo_movimento_display(self, obj):
        colors = {
            'abertura': 'blue', 'fechamento': 'purple', 'venda': 'green',
            'recebimento': 'green', 'pagamento': 'red', 'sangria': 'orange',
            'suprimento': 'blue', 'cancelamento': 'gray'
        }
        icons = {
            'abertura': '🔓', 'fechamento': '🔒', 'venda': '💰',
            'recebimento': '📥', 'pagamento': '📤', 'sangria': '💸',
            'suprimento': '💰', 'cancelamento': '❌'
        }
        color = colors.get(obj.tipo_movimento, 'gray')
        icon = icons.get(obj.tipo_movimento, '📄')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_tipo_movimento_display()
        )
    tipo_movimento_display.short_description = 'Tipo'
    
    def valor_display(self, obj):
        color = 'green' if obj.valor >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, format_money(obj.valor)
        )
    valor_display.short_description = "Valor"
    
    def forma_pagamento_display(self, obj):
        icons = {
            'dinheiro': '💵', 'kwik': '📱', 'cartao_debito': '💳',
            'cartao_credito': '💳', 'transferencia': '🔄', 'cheque': '📝'
        }
        icon = icons.get(obj.forma_pagamento, '💰')
        
        return format_html(
            '{} {}', icon, obj.get_forma_pagamento_display()
        )
    forma_pagamento_display.short_description = 'Forma'
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'confirmado': 'green',
            'cancelado': 'red',
            'estornado': 'gray'
        }
        icons = {
            'pendente': '⏳',
            'confirmado': '✅',
            'cancelado': '❌',
            'estornado': '🔄'
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def confirmar_movimentos(self, request, queryset):
        confirmados = 0
        for movimento in queryset.filter(status='pendente'):
            try:
                movimento.confirmar_movimento(request.user)
                confirmados += 1
            except Exception as e:
                messages.error(request, f'Erro ao confirmar movimento {movimento.numero_movimento}: {e}')
        
        if confirmados:
            messages.success(request, f'{confirmados} movimentos confirmados.')
    confirmar_movimentos.short_description = "Confirmar movimentos selecionados"
    
    def estornar_movimentos(self, request, queryset):
        estornados = 0
        for movimento in queryset.filter(status='confirmado'):
            try:
                movimento.estornar_movimento("Estorno via admin", request.user)
                estornados += 1
            except Exception as e:
                messages.error(request, f'Erro ao estornar movimento {movimento.numero_movimento}: {e}')
        
        if estornados:
            messages.success(request, f'{estornados} movimentos estornados.')
    estornar_movimentos.short_description = "Estornar movimentos selecionados"
    
    def gerar_fechamento_caixa(self, request, queryset):
        lojas = queryset.values('loja').distinct()
        for loja_data in lojas:
            loja_id = loja_data['loja']
            saldo = MovimentoCaixa.calcular_saldo_caixa(loja_id)
            messages.info(request, f'Loja {loja_id}: Saldo atual do caixa: {format_money(saldo)}')
    gerar_fechamento_caixa.short_description = "Gerar fechamento de caixa"

# =====================================
# IMPOSTO/TRIBUTO
# =====================================

@admin.register(ImpostoTributo)
class ImpostoTributoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_imposto', 'tipo_imposto_display', 'periodo_display', 
        'valor_devido_display', 'situacao_display', 'dias_vencimento_display'
    ]
    list_filter = [
        'tipo_imposto', 'situacao', 'regime_tributario', 'ano_referencia', 
        'mes_referencia', 'calculo_automatico'
    ]
    search_fields = ['codigo_imposto', 'nome', 'numero_darf', 'observacoes']
    readonly_fields = [
        'codigo_imposto', 'valor_calculado', 'total', 'percentual_pago',
        'dias_para_vencimento', 'esta_vencido'
    ]
    date_hierarchy = 'data_vencimento'
    ordering = ['-ano_referencia', '-mes_referencia', 'data_vencimento']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_imposto', 'nome', 'tipo_imposto', 'descricao')
        }),
        ('Regime e Periodicidade', {
            'fields': ('regime_tributario', 'periodicidade')
        }),
        ('Período de Apuração', {
            'fields': ('ano_referencia', 'mes_referencia', 'data_inicio_periodo', 'data_fim_periodo')
        }),
        ('Datas Importantes', {
            'fields': ('data_vencimento', 'data_pagamento', 'data_calculo')
        }),
        ('Método de Cálculo', {
            'fields': ('metodo_calculo', 'aliquota_percentual', 'valor_fixo')
        }),
        ('Base de Cálculo', {
            'fields': ('base_calculo', 'receita_bruta', 'deducoes')
        }),
        ('Valores Calculados', {
            'fields': ('valor_calculado', 'valor_devido', 'valor_pago', 'percentual_pago')
        }),
        ('Multas e Juros', {
            'fields': ('valor_multa', 'valor_juros', 'total')
        }),
        ('Compensações', {
            'fields': ('creditos_periodo_anterior', 'compensacoes')
        }),
        ('Situação', {
            'fields': ('situacao', 'dias_para_vencimento', 'esta_vencido')
        }),
        ('DARF/Guia', {
            'fields': ('numero_darf', 'codigo_receita', 'numero_referencia'),
            'classes': ['collapse']
        }),
        ('Relacionamentos', {
            'fields': ('conta_bancaria_pagamento', 'movimentacao_pagamento', 'plano_contas', 'centro_custo')
        }),
        ('Controle', {
            'fields': ('calculo_automatico', 'ultima_atualizacao_calculo', 'usuario_responsavel')
        }),
        ('Anexos', {
            'fields': ('arquivo_guia', 'arquivo_comprovante'),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
    )
    
    actions = ['calcular_impostos', 'gerar_darf', 'marcar_como_pago', 'apurar_periodo']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'plano_contas', 'centro_custo', 'conta_bancaria_pagamento', 'usuario_responsavel', 'empresa'
        )
    
    def periodo_display(self, obj):
        return f"{obj.mes_referencia:02d}/{obj.ano_referencia}"
    periodo_display.short_description = "Período"
    
    def tipo_imposto_display(self, obj):
        colors = {
            'simples_nacional': 'blue', 'pis': 'green', 'cofins': 'green',
            'iss': 'purple', 'irpj': 'red', 'csll': 'orange'
        }
        color = colors.get(obj.tipo_imposto, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_tipo_imposto_display()
        )
    tipo_imposto_display.short_description = 'Tipo'
    
    def valor_devido_display(self, obj):
        return format_html('<span>{}</span>', format_money(obj.valor_devido))
    valor_devido_display.short_description = "Valor Devido"
    
    def situacao_display(self, obj):
        colors = {
            'pendente': 'orange', 'calculado': 'blue', 'apurado': 'purple',
            'pago': 'green', 'parcelado': 'yellow', 'vencido': 'red',
            'isento': 'gray', 'suspenso': 'gray'
        }
        icons = {
            'pendente': '⏳', 'calculado': '🧮', 'apurado': '📊',
            'pago': '✅', 'parcelado': '📅', 'vencido': '⚠️',
            'isento': '🚫', 'suspenso': '⏸️'
        }
        color = colors.get(obj.situacao, 'gray')
        icon = icons.get(obj.situacao, '')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_situacao_display()
        )
    situacao_display.short_description = 'Situação'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_para_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} dias em atraso</span>',
                abs(dias)
            )
        elif dias == 0:
            return format_html('<span style="color: orange; font-weight: bold;">🕐 Vence hoje</span>')
        elif dias <= 7:
            return format_html(
                '<span style="color: orange;">⏰ Vence em {} dias</span>',
                dias
            )
        else:
            return format_html('<span style="color: green;">📅 Vence em {} dias</span>', dias)
    dias_vencimento_display.short_description = 'Vencimento'
    
    def calcular_impostos(self, request, queryset):
        calculados = 0
        for imposto in queryset:
            try:
                imposto.calcular_imposto(forcar_recalculo=True)
                calculados += 1
            except Exception as e:
                messages.error(request, f'Erro ao calcular imposto {imposto.codigo_imposto}: {e}')
        
        messages.success(request, f'{calculados} impostos calculados.')
    calcular_impostos.short_description = "Calcular impostos selecionados"
    
    def gerar_darf(self, request, queryset):
        gerados = 0
        for imposto in queryset.filter(situacao__in=['calculado', 'apurado']):
            imposto.gerar_darf()
            gerados += 1
        
        messages.success(request, f'{gerados} DARFs gerados.')
    gerar_darf.short_description = "Gerar DARF"
    
    def marcar_como_pago(self, request, queryset):
        pagos = 0
        for imposto in queryset.filter(situacao__in=['calculado', 'apurado', 'vencido']):
            imposto.valor_pago = imposto.total
            imposto.situacao = 'pago'
            imposto.data_pagamento = date.today()
            imposto.save()
            pagos += 1
        
        messages.success(request, f'{pagos} impostos marcados como pagos.')
    marcar_como_pago.short_description = "Marcar como pago"
    
    def apurar_periodo(self, request, queryset):
        apurados = queryset.filter(situacao='calculado').update(situacao='apurado')
        messages.success(request, f'{apurados} impostos apurados.')
    apurar_periodo.short_description = "Apurar período"

# =====================================
# CONFIGURAÇÃO DE IMPOSTOS
# =====================================

@admin.register(ConfiguracaoImposto)
class ConfiguracaoImpostoAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'regime_tributario_display', 'anexo_simples', 
        'cnae_principal', 'gerar_impostos_automaticamente'
    ]
    list_filter = ['regime_tributario', 'anexo_simples', 'gerar_impostos_automaticamente']
    search_fields = ['empresa__nome', 'cnae_principal', 'observacoes']
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Regime Tributário', {
            'fields': ('regime_tributario', 'anexo_simples', 'cnae_principal')
        }),
        ('Alíquotas Padrão', {
            'fields': ('aliquota_pis', 'aliquota_cofins', 'aliquota_iss')
        }),
        ('Configurações Automáticas', {
            'fields': ('gerar_impostos_automaticamente', 'dia_vencimento_impostos')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('empresa')
    
    def regime_tributario_display(self, obj):
        colors = {
            'simples_nacional': 'blue',
            'lucro_presumido': 'green',
            'lucro_real': 'red',
            'mei': 'purple'
        }
        color = colors.get(obj.regime_tributario, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_regime_tributario_display()
        )
    regime_tributario_display.short_description = 'Regime'

# =====================================
# CONFIGURAÇÕES GERAIS DO ADMIN
# =====================================

admin.site.site_header = "Sistema Financeiro - Administração"
admin.site.site_title = "Financeiro Admin"
admin.site.index_title = "Gestão Financeira"