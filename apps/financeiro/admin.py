# apps/financeiro/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import csv
from datetime import date, timedelta
from .models import (
    PlanoContas, CentroCusto, ContaBancaria, MovimentacaoFinanceira,
    ContaPai, ContaPagar, ContaReceber, FluxoCaixa, ConciliacaoBancaria,
    OrcamentoFinanceiro, CategoriaFinanceira, LancamentoFinanceiro,
    MovimentoCaixa, ImpostoTributo, ConfiguracaoImposto
)

# ============================================================================
# PLANO DE CONTAS
# ============================================================================

@admin.register(PlanoContas)
class PlanoContasAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_formatado',
        'nome_hierarquico',
        'tipo_conta_badge',
        'natureza_badge',
        'aceita_lancamento_icon',
        'nivel_display',
        'ativa_status',
        'saldo_atual'
    ]
    
    list_filter = [
        'tipo_conta',
        'natureza',
        'aceita_lancamento',
        'ativa',
        'nivel',
        'empresa'
    ]
    
    search_fields = [
        'codigo',
        'nome',
        'descricao'
    ]
    
    readonly_fields = [
        'nivel',
        'codigo_completo',
        'nome_completo'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'codigo',
                'nome',
                'descricao',
                'empresa'
            )
        }),
        ('Hierarquia', {
            'fields': (
                'conta_pai',
                'nivel',
                'codigo_completo',
                'nome_completo'
            )
        }),
        ('Características', {
            'fields': (
                'tipo_conta',
                'natureza',
                'aceita_lancamento'
            )
        }),
        ('Configurações', {
            'fields': (
                'ativa',
                'ordem'
            )
        })
    )
    
    actions = [
        'ativar_contas',
        'desativar_contas',
        'exportar_plano_contas'
    ]
    
    def codigo_formatado(self, obj):
        return format_html(
            '<code style="background-color: #f1f5f9; padding: 2px 6px; border-radius: 3px; font-family: monospace;">{}</code>',
            obj.codigo
        )
    codigo_formatado.short_description = 'Código'
    codigo_formatado.admin_order_field = 'codigo'
    
    def nome_hierarquico(self, obj):
        indent = '&nbsp;&nbsp;' * (obj.nivel - 1)
        return format_html(f'{indent}<strong>{obj.nome}</strong>')
    nome_hierarquico.short_description = 'Nome'
    nome_hierarquico.admin_order_field = 'nome'
    
    def tipo_conta_badge(self, obj):
        cores = {
            'receita': '#10b981',
            'despesa': '#ef4444',
            'ativo': '#3b82f6',
            'passivo': '#f59e0b',
            'patrimonio': '#8b5cf6'
        }
        cor = cores.get(obj.tipo_conta, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            cor,
            obj.get_tipo_conta_display()
        )
    tipo_conta_badge.short_description = 'Tipo'
    
    def natureza_badge(self, obj):
        cor = '#3b82f6' if obj.natureza == 'debito' else '#10b981'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            cor,
            obj.get_natureza_display()
        )
    natureza_badge.short_description = 'Natureza'
    
    def aceita_lancamento_icon(self, obj):
        if obj.aceita_lancamento:
            return format_html('<span style="color: #10b981;">✓ Sim</span>')
        return format_html('<span style="color: #ef4444;">✗ Não</span>')
    aceita_lancamento_icon.short_description = 'Aceita Lançamento'
    
    def nivel_display(self, obj):
        return format_html(
            '<span style="background-color: #f1f5f9; padding: 2px 6px; border-radius: 3px; font-weight: bold;">Nível {}</span>',
            obj.nivel
        )
    nivel_display.short_description = 'Nível'
    
    def ativa_status(self, obj):
        if obj.ativa:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Ativa</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">✗ Inativa</span>')
    ativa_status.short_description = 'Status'
    
    def saldo_atual(self, obj):
        # Calcular saldo baseado nos lançamentos
        return format_html('<span style="font-family: monospace;">R$ 0,00</span>')
    saldo_atual.short_description = 'Saldo Atual'
    
    def ativar_contas(self, request, queryset):
        count = queryset.update(ativa=True)
        self.message_user(request, f'{count} contas ativadas com sucesso.', messages.SUCCESS)
    ativar_contas.short_description = 'Ativar contas selecionadas'
    
    def desativar_contas(self, request, queryset):
        count = queryset.update(ativa=False)
        self.message_user(request, f'{count} contas desativadas com sucesso.', messages.SUCCESS)
    desativar_contas.short_description = 'Desativar contas selecionadas'
    
    def exportar_plano_contas(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="plano_contas.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Código', 'Nome', 'Tipo', 'Natureza', 'Ativa', 'Aceita Lançamento'])
        
        for conta in queryset:
            writer.writerow([
                conta.codigo,
                conta.nome,
                conta.get_tipo_conta_display(),
                conta.get_natureza_display(),
                'Sim' if conta.ativa else 'Não',
                'Sim' if conta.aceita_lancamento else 'Não'
            ])
        
        return response
    exportar_plano_contas.short_description = 'Exportar plano de contas (CSV)'

# ============================================================================
# CENTRO DE CUSTO
# ============================================================================

@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_formatado',
        'nome',
        'responsavel_info',
        'loja_info',
        'ativo_status',
        'total_movimentacoes'
    ]
    
    list_filter = [
        'ativo',
        'loja',
        'empresa'
    ]
    
    search_fields = [
        'codigo',
        'nome',
        'descricao',
        'responsavel__first_name',
        'responsavel__last_name'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'codigo',
                'nome',
                'descricao',
                'empresa'
            )
        }),
        ('Responsabilidade', {
            'fields': (
                'responsavel',
                'loja'
            )
        }),
        ('Status', {
            'fields': (
                'ativo',
            )
        })
    )
    
    def codigo_formatado(self, obj):
        return format_html(
            '<code style="background-color: #f1f5f9; padding: 2px 6px; border-radius: 3px;">{}</code>',
            obj.codigo
        )
    codigo_formatado.short_description = 'Código'
    
    def responsavel_info(self, obj):
        if obj.responsavel:
            return format_html(
                '<div><strong>{}</strong><br><small>{}</small></div>',
                obj.responsavel.get_full_name(),
                obj.responsavel.email
            )
        return format_html('<span style="color: #6b7280;">Sem responsável</span>')
    responsavel_info.short_description = 'Responsável'
    
    def loja_info(self, obj):
        if obj.loja:
            return obj.loja.nome
        return format_html('<span style="color: #6b7280;">Todas as lojas</span>')
    loja_info.short_description = 'Loja'
    
    def ativo_status(self, obj):
        if obj.ativo:
            return format_html('<span style="color: #10b981;">✓ Ativo</span>')
        return format_html('<span style="color: #ef4444;">✗ Inativo</span>')
    ativo_status.short_description = 'Status'
    
    def total_movimentacoes(self, obj):
        # Contar movimentações do centro de custo
        return format_html('<span style="font-family: monospace;">0</span>')
    total_movimentacoes.short_description = 'Movimentações'

# ============================================================================
# CONTA BANCÁRIA
# ============================================================================

@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = [
        'conta_info',
        'banco',
        'tipo_conta_badge',
        'saldo_atual_display',
        'saldo_disponivel_display',
        'conta_principal_icon',
        'ativa_status',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'tipo_conta',
        'ativa',
        'conta_principal',
        'permite_saldo_negativo',
        'empresa'
    ]
    
    search_fields = [
        'nome',
        'banco',
        'agencia',
        'conta',
        'observacoes'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'nome',
                'banco',
                ('agencia', 'conta', 'digito'),
                'tipo_conta',
                'empresa'
            )
        }),
        ('Saldos e Limites', {
            'fields': (
                'saldo_inicial',
                'saldo_atual',
                'limite_credito',
                'saldo_disponivel'
            )
        }),
        ('Configurações', {
            'fields': (
                'ativa',
                'conta_principal',
                'permite_saldo_negativo'
            )
        }),
        ('Integração', {
            'fields': (
                'codigo_integracao',
                'ultima_conciliacao'
            ),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': (
                'observacoes',
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = [
        'saldo_atual',
        'saldo_disponivel'
    ]
    
    actions = [
        'atualizar_saldos',
        'marcar_como_principal',
        'conciliar_contas'
    ]
    
    def conta_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small>Ag: {} Cc: {}{}</small>'
            '</div>',
            obj.nome,
            obj.agencia,
            obj.conta,
            f'-{obj.digito}' if obj.digito else ''
        )
    conta_info.short_description = 'Conta'
    
    def tipo_conta_badge(self, obj):
        cores = {
            'corrente': '#3b82f6',
            'poupanca': '#10b981',
            'investimento': '#8b5cf6',
            'cartao': '#f59e0b',
            'caixa': '#6b7280'
        }
        cor = cores.get(obj.tipo_conta, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            cor,
            obj.get_tipo_conta_display()
        )
    tipo_conta_badge.short_description = 'Tipo'
    
    def saldo_atual_display(self, obj):
        cor = '#10b981' if obj.saldo_atual >= 0 else '#ef4444'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-family: monospace;">AOA {:,.2f}</span>',
            cor,
            obj.saldo_atual
        )
    saldo_atual_display.short_description = 'Saldo Atual'
    
    def saldo_disponivel_display(self, obj):
        return format_html(
            '<span style="font-family: monospace; color: #059669;">AOA {:,.2f}</span>',
            obj.saldo_disponivel
        )
    saldo_disponivel_display.short_description = 'Saldo Disponível'
    
    def conta_principal_icon(self, obj):
        if obj.conta_principal:
            return format_html('<span style="color: #f59e0b; font-size: 16px;">★ Principal</span>')
        return format_html('<span style="color: #d1d5db;">☆</span>')
    conta_principal_icon.short_description = 'Principal'
    
    def ativa_status(self, obj):
        if obj.ativa:
            return format_html('<span style="color: #10b981;">✓ Ativa</span>')
        return format_html('<span style="color: #ef4444;">✗ Inativa</span>')
    ativa_status.short_description = 'Status'
    
    def acoes_rapidas(self, obj):
        buttons = []
        
        buttons.append(
            f'<a href="#" onclick="atualizarSaldo({obj.pk})" '
            f'style="background-color: #3b82f6; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">'
            f'🔄 Atualizar</a>'
        )
        
        buttons.append(
            f'<a href="#" onclick="conciliarConta({obj.pk})" '
            f'style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">'
            f'📊 Conciliar</a>'
        )
        
        return format_html(''.join(buttons))
    acoes_rapidas.short_description = 'Ações'
    
    def atualizar_saldos(self, request, queryset):
        count = 0
        for conta in queryset:
            conta.atualizar_saldo()
            count += 1
        
        self.message_user(request, f'Saldos de {count} contas atualizados.', messages.SUCCESS)
    atualizar_saldos.short_description = 'Atualizar saldos das contas'
    
    def marcar_como_principal(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, 'Selecione apenas uma conta para marcar como principal.', messages.ERROR)
            return
        
        # Desmarcar todas as outras contas principais
        ContaBancaria.objects.filter(empresa=queryset.first().empresa).update(conta_principal=False)
        
        # Marcar a selecionada como principal
        queryset.update(conta_principal=True)
        
        self.message_user(request, 'Conta marcada como principal.', messages.SUCCESS)
    marcar_como_principal.short_description = 'Marcar como conta principal'

# ============================================================================
# MOVIMENTAÇÃO FINANCEIRA
# ============================================================================

@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimentacao',
        'tipo_valor_display',
        'conta_bancaria',
        'descricao_curta',
        'pessoa_relacionada',
        'status_badge',
        'confirmada_icon',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'tipo_movimentacao',
        'tipo_documento',
        'status',
        'confirmada',
        'conciliada',
        'data_movimentacao',
        'conta_bancaria',
        'empresa'
    ]
    
    search_fields = [
        'numero_documento',
        'descricao',
        'observacoes',
        'cliente__nome',
        'fornecedor__nome_fantasia'
    ]
    
    date_hierarchy = 'data_movimentacao'
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'numero_documento',
                'tipo_movimentacao',
                'tipo_documento',
                'empresa'
            )
        }),
        ('Datas', {
            'fields': (
                'data_movimentacao',
                'data_vencimento',
                'data_confirmacao'
            )
        }),
        ('Valores', {
            'fields': (
                'valor',
                ('valor_juros', 'valor_multa', 'valor_desconto'),
                'total'
            )
        }),
        ('Contas', {
            'fields': (
                'conta_bancaria',
                'conta_destino',
                'plano_contas',
                'centro_custo'
            )
        }),
        ('Relacionamentos', {
            'fields': (
                'fornecedor',
                'cliente',
                'venda_relacionada'
            )
        }),
        ('Descrição', {
            'fields': (
                'descricao',
                'observacoes'
            )
        }),
        ('Controle', {
            'fields': (
                'status',
                'confirmada',
                'conciliada',
                'data_conciliacao',
                'usuario_responsavel'
            )
        }),
        ('Dados do Cheque', {
            'fields': (
                'numero_cheque',
                'banco_cheque',
                'emissor_cheque'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = [
        'total',
        'data_confirmacao'
    ]
    
    actions = [
        'confirmar_movimentacoes',
        'estornar_movimentacoes',
        'exportar_extrato'
    ]
    
    def tipo_valor_display(self, obj):
        sinal = '+' if obj.tipo_movimentacao == 'entrada' else '-'
        cor = '#10b981' if obj.tipo_movimentacao == 'entrada' else '#ef4444'
        
        return format_html(
            '<div style="text-align: right;">'
            '<span style="color: {}; font-weight: bold; font-family: monospace;">{} AOA {:,.2f}</span><br>'
            '<small style="color: #6b7280;">{}</small>'
            '</div>',
            cor,
            sinal,
            obj.valor,
            obj.get_tipo_movimentacao_display()
        )
    tipo_valor_display.short_description = 'Tipo/Valor'
    
    def descricao_curta(self, obj):
        descricao = obj.descricao[:40] + '...' if len(obj.descricao) > 40 else obj.descricao
        return format_html('<span title="{}">{}</span>', obj.descricao, descricao)
    descricao_curta.short_description = 'Descrição'
    
    def pessoa_relacionada(self, obj):
        if obj.cliente:
            return format_html('<span style="color: #10b981;">👤 {}</span>', obj.cliente.nome)
        elif obj.fornecedor:
            return format_html('<span style="color: #ef4444;">🏢 {}</span>', obj.fornecedor.nome_fantasia)
        return format_html('<span style="color: #6b7280;">-</span>')
    pessoa_relacionada.short_description = 'Cliente/Fornecedor'
    
    def status_badge(self, obj):
        cores = {
            'pendente': '#f59e0b',
            'confirmada': '#10b981',
            'cancelada': '#6b7280',
            'estornada': '#ef4444'
        }
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def confirmada_icon(self, obj):
        if obj.confirmada:
            return format_html('<span style="color: #10b981; font-size: 16px;">✓</span>')
        return format_html('<span style="color: #f59e0b; font-size: 16px;">⏳</span>')
    confirmada_icon.short_description = 'Confirmada'
    
    def acoes_rapidas(self, obj):
        buttons = []
        
        if not obj.confirmada and obj.status == 'pendente':
            buttons.append(
                f'<a href="#" onclick="confirmarMovimentacao({obj.pk})" '
                f'style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">'
                f'✓ Confirmar</a>'
            )
        
        if obj.confirmada and obj.status == 'confirmada':
            buttons.append(
                f'<a href="#" onclick="estornarMovimentacao({obj.pk})" '
                f'style="background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">'
                f'↩️ Estornar</a>'
            )
        
        return format_html(''.join(buttons))
    acoes_rapidas.short_description = 'Ações'
    
    def confirmar_movimentacoes(self, request, queryset):
        count = 0
        for mov in queryset.filter(status='pendente', confirmada=False):
            try:
                mov.confirmar_movimentacao(request.user)
                count += 1
            except ValidationError as e:
                self.message_user(request, f'Erro ao confirmar {mov}: {e}', messages.ERROR)
        
        if count:
            self.message_user(request, f'{count} movimentações confirmadas.', messages.SUCCESS)
    confirmar_movimentacoes.short_description = 'Confirmar movimentações selecionadas'

# ============================================================================
# CONTAS A PAGAR
# ============================================================================

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento',
        'descricao_curta',
        'fornecedor_info',
        'valor_info',
        'vencimento_info',
        'status_badge',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'status',
        'tipo_conta',
        'data_vencimento',
        'data_emissao',
        'fornecedor',
        'empresa'
    ]
    
    search_fields = [
        'numero_documento',
        'descricao',
        'fornecedor__nome_fantasia',
        'observacoes'
    ]
    
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'numero_documento',
                'descricao',
                'tipo_conta',
                'empresa'
            )
        }),
        ('Datas', {
            'fields': (
                'data_emissao',
                'data_vencimento',
                'data_pagamento'
            )
        }),
        ('Valores', {
            'fields': (
                'valor_original',
                ('valor_juros', 'valor_multa', 'valor_desconto'),
                'valor_pago',
                'valor_saldo'
            )
        }),
        ('Relacionamentos', {
            'fields': (
                'fornecedor',
                'plano_contas',
                'centro_custo'
            )
        }),
        ('Parcelamento', {
            'fields': (
                ('numero_parcela', 'total_parcelas'),
                'conta_pai'
            ),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': (
                'status',
                'observacoes'
            )
        })
    )
    
    readonly_fields = [
        'valor_saldo',
        'data_pagamento'
    ]
    
    actions = [
        'marcar_como_paga',
        'gerar_relatorio_vencimentos',
        'exportar_contas_pagar'
    ]
    
    def descricao_curta(self, obj):
        return obj.descricao[:30] + '...' if len(obj.descricao) > 30 else obj.descricao
    descricao_curta.short_description = 'Descrição'
    
    def fornecedor_info(self, obj):
        if obj.fornecedor:
            return format_html(
                '<div><strong>{}</strong><br><small>{}</small></div>',
                obj.fornecedor.nome_fantasia,
                obj.fornecedor.cnpj or obj.fornecedor.cpf
            )
        return format_html('<span style="color: #6b7280;">Sem fornecedor</span>')
    fornecedor_info.short_description = 'Fornecedor'
    
    def valor_info(self, obj):
        return format_html(
            '<div style="text-align: right; font-family: monospace;">'
            '<strong>AOA {:,.2f}</strong><br>'
            '<small style="color: {};">Saldo: AOA {:,.2f}</small>'
            '</div>',
            obj.valor_original,
            '#10b981' if obj.valor_saldo <= 0 else '#ef4444',
            obj.valor_saldo
        )
    valor_info.short_description = 'Valores'
    
    def vencimento_info(self, obj):
        hoje = date.today()
        dias = (obj.data_vencimento - hoje).days
        
        if dias < 0:
            cor = '#ef4444'
            status = f'Vencida há {abs(dias)} dias'
        elif dias == 0:
            cor = '#f59e0b'
            status = 'Vence hoje'
        elif dias <= 7:
            cor = '#f59e0b'
            status = f'Vence em {dias} dias'
        else:
            cor = '#6b7280'
            status = f'Vence em {dias} dias'
        
        return format_html(
            '<div style="text-align: center;">'
            '<strong>{}</strong><br>'
            '<small style="color: {};">{}</small>'
            '</div>',
            obj.data_vencimento.strftime('%d/%m/%Y'),
            cor,
            status
        )
    vencimento_info.short_description = 'Vencimento'
    
    def status_badge(self, obj):
        cores = {
            'aberta': '#3b82f6',
            'vencida': '#ef4444',
            'paga': '#10b981',
            'cancelada': '#6b7280',
            'renegociada': '#f59e0b'
        }
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def acoes_rapidas(self, obj):
        buttons = []
        
        if obj.status in ['aberta', 'vencida']:
            buttons.append(
                f'<a href="#" onclick="pagarConta({obj.pk})" '
                f'style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">'
                f'💰 Pagar</a>'
            )
        
        return format_html(''.join(buttons))
    acoes_rapidas.short_description = 'Ações'

# ============================================================================
# CONTAS A RECEBER
# ============================================================================




@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = [
        'numero_documento',
        'descricao_curta',
        'cliente_info',
        'valor_info',
        'vencimento_info',
        'status_badge',
        'acoes_rapidas'
    ]

    def descricao_curta(self, obj):
        return obj.descricao[:40] + '...' if len(obj.descricao) > 40 else obj.descricao
    descricao_curta.short_description = 'Descrição'

    def valor_info(self, obj):
        return f"R$ {obj.valor_original:,.2f}"
    valor_info.short_description = 'Valor'

    def vencimento_info(self, obj):
        dias = (obj.data_vencimento - date.today()).days
        if dias < 0:
            return format_html('<span style="color:red;">{:%d/%m/%Y} ({} dias vencida)</span>', obj.data_vencimento, abs(dias))
        elif dias == 0:
            return format_html('<span style="color:orange;">Vence hoje</span>')
        else:
            return format_html('<span style="color:green;">{:%d/%m/%Y} (em {} dias)</span>', obj.data_vencimento, dias)
    vencimento_info.short_description = 'Vencimento'

    def status_badge(self, obj):
        cores = {
            'aberta': '#3b82f6',
            'vencida': '#ef4444',
            'recebida': '#22c55e',
            'cancelada': '#6b7280',
            'renegociada': '#f59e0b',
        }
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:8px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def acoes_rapidas(self, obj):
        return format_html(
            '<a href="/admin/financeiro/contareceber/{}/change/">Editar</a> | '
            '<a href="/admin/financeiro/contareceber/{}/delete/">Excluir</a>',
            obj.id, obj.id
        )
    acoes_rapidas.short_description = 'Ações'



# ============================================================================
# MOVIMENTO DE CAIXA
# ============================================================================

@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_movimento',
        'data_hora_display',
        'tipo_valor_display',
        'forma_pagamento_badge',
        'usuario_info',
        'loja',
        'status_badge',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'tipo_movimento',
        'forma_pagamento',
        'status',
        'confirmado',
        'data_movimento',
        'loja',
        'empresa'
    ]
    
    search_fields = [
        'numero_movimento',
        'descricao',
        'observacoes',
        'numero_documento',
        'cliente__nome'
    ]
    
    date_hierarchy = 'data_movimento'
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'numero_movimento',
                'data_movimento',
                'hora_movimento',
                'empresa'
            )
        }),
        ('Tipo e Forma', {
            'fields': (
                'tipo_movimento',
                'forma_pagamento'
            )
        }),
        ('Valores', {
            'fields': (
                'valor',
                'valor_troco'
            )
        }),
        ('Descrição', {
            'fields': (
                'descricao',
                'observacoes'
            )
        }),
        ('Relacionamentos', {
            'fields': (
                'usuario',
                'loja',
                'venda_relacionada',
                'cliente',
                'fornecedor'
            )
        }),
        ('Contas Financeiras', {
            'fields': (
                'conta_receber',
                'conta_pagar'
            ),
            'classes': ('collapse',)
        }),
        ('Status e Controle', {
            'fields': (
                'status',
                'confirmado',
                'data_confirmacao'
            )
        }),
        ('Dados do Documento', {
            'fields': (
                'numero_documento',
                ('numero_cheque', 'banco_cheque'),
                'emissor_cheque',
                'data_cheque'
            ),
            'classes': ('collapse',)
        }),
        ('Dados do Cartão', {
            'fields': (
                'numero_cartao_mascarado',
                'bandeira_cartao',
                'numero_autorizacao',
                'numero_comprovante'
            ),
            'classes': ('collapse',)
        }),
        ('Estorno', {
            'fields': (
                'movimento_original',
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = [
        'numero_movimento',
        'hora_movimento',
        'data_confirmacao'
    ]
    
    actions = [
        'confirmar_movimentos',
        'estornar_movimentos',
        'fechar_caixa',
        'exportar_movimentos_caixa'
    ]
    
    def data_hora_display(self, obj):
        return format_html(
            '<div>'
            '<strong>{}</strong><br>'
            '<small>{}</small>'
            '</div>',
            obj.data_movimento.strftime('%d/%m/%Y'),
            obj.hora_movimento.strftime('%H:%M:%S')
        )
    data_hora_display.short_description = 'Data/Hora'
    
    def tipo_valor_display(self, obj):
        sinal = '+' if obj.valor >= 0 else ''
        cor = '#10b981' if obj.valor >= 0 else '#ef4444'
        
        return format_html(
            '<div style="text-align: right;">'
            '<span style="color: {}; font-weight: bold; font-family: monospace;">{} AOA {:,.2f}</span><br>'
            '<small style="color: #6b7280;">{}</small>'
            '</div>',
            cor,
            sinal,
            abs(obj.valor),
            obj.get_tipo_movimento_display()
        )
    tipo_valor_display.short_description = 'Tipo/Valor'
    
    def forma_pagamento_badge(self, obj):
        cores = {
            'dinheiro': '#10b981',
            'cartao_debito': '#3b82f6',
            'cartao_credito': '#8b5cf6',
            'transferencia': '#f59e0b',
            'cheque': '#6b7280',
            'vale': '#ef4444',
            'outros': '#6b7280'
        }
        cor = cores.get(obj.forma_pagamento, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            cor,
            obj.get_forma_pagamento_display()
        )
    forma_pagamento_badge.short_description = 'Forma'
    
    def usuario_info(self, obj):
        return format_html(
            '<div><strong>{}</strong></div>',
            obj.usuario.get_full_name() or obj.usuario.username
        )
    usuario_info.short_description = 'Usuário'
    
    def status_badge(self, obj):
        cores = {
            'pendente': '#f59e0b',
            'confirmado': '#10b981',
            'cancelado': '#6b7280',
            'estornado': '#ef4444'
        }
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def acoes_rapidas(self, obj):
        buttons = []
        
        if not obj.confirmado and obj.status == 'pendente':
            buttons.append(
                f'<a href="#" onclick="confirmarMovimento({obj.pk})" '
                f'style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">'
                f'✓ Confirmar</a>'
            )
        
        if obj.confirmado and obj.status == 'confirmado':
            buttons.append(
                f'<a href="#" onclick="estornarMovimento({obj.pk})" '
                f'style="background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">'
                f'↩️ Estornar</a>'
            )
        
        return format_html(''.join(buttons))
    acoes_rapidas.short_description = 'Ações'

# ============================================================================
# IMPOSTO TRIBUTO
# ============================================================================

@admin.register(ImpostoTributo)
class ImpostoTributoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_receita_agt_formatado',
        'nome_imposto_curto',
        'periodo_referencia',
        'regime_tributario_badge',
        'valor_devido_formatado',
        'situacao_badge',
        'dias_vencimento_badge',
        'percentual_pago_progress',
        'acoes_rapidas'
    ]
    
    list_filter = [
        'situacao',
        'codigo_receita_agt',
        'regime_tributario',
        'ano_referencia',
        'periodicidade',
        'calculo_automatico',
        'data_vencimento',
        'empresa',
    ]
    
    search_fields = [
        'nome',
        'codigo_receita_agt',
        'codigo_imposto_interno',
        'numero_guia_agt',
        'numero_declaracao_agt',
        'observacoes',
    ]
    
    readonly_fields = [
        'codigo_imposto_interno',
        'valor_calculado',
        'total_agt',
        'data_calculo',
        'ultima_atualizacao_calculo',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('🇦🇴 Identificação AGT', {
            'fields': (
                'codigo_receita_agt',
                'codigo_imposto_interno',
                'nome',
                'descricao',
                'empresa',
            )
        }),
        
        ('📋 Regime e Período', {
            'fields': (
                ('regime_tributario', 'periodicidade'),
                ('ano_referencia', 'mes_referencia'),
                ('data_inicio_periodo', 'data_fim_periodo'),
                'data_vencimento',
            )
        }),
        
        ('💰 Cálculo e Valores (AOA)', {
            'fields': (
                ('metodo_calculo', 'calculo_automatico'),
                ('aliquota_percentual', 'valor_fixo'),
                ('receita_bruta', 'base_calculo'),
                'deducoes_permitidas',
                ('valor_calculado', 'data_calculo'),
                ('valor_devido', 'situacao'),
            )
        }),
        
        ('🔢 Compensações e Créditos', {
            'fields': (
                'creditos_periodo_anterior',
                'compensacoes_utilizadas',
            ),
            'classes': ('collapse',),
        }),
        
        ('⚠️ Multas e Juros', {
            'fields': (
                ('valor_multa', 'valor_juros'),
                'total_agt',
            ),
            'classes': ('collapse',),
        }),
        
        ('💳 Pagamento', {
            'fields': (
                ('valor_pago', 'data_pagamento'),
                'conta_bancaria_pagamento',
                'movimentacao_pagamento',
            ),
            'classes': ('collapse',),
        }),
        
        ('📄 Documentos AGT', {
            'fields': (
                'numero_guia_agt',
                'numero_declaracao_agt',
                'data_declaracao',
                'arquivo_declaracao_agt',
                'arquivo_guia_pagamento',
                'arquivo_comprovante_pagamento',
            ),
            'classes': ('collapse',),
        }),
        
        ('🏢 Contabilidade', {
            'fields': (
                'plano_contas',
                'centro_custo',
            ),
            'classes': ('collapse',),
        }),
        
        ('📝 Controle e Observações', {
            'fields': (
                'usuario_responsavel',
                'observacoes',
                'ultima_atualizacao_calculo',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'calcular_impostos_selecionados',
        'marcar_como_pago',
        'gerar_guias_pagamento',
        'exportar_para_agt',
    ]
    
    # Métodos de exibição específicos do ImpostoTributo
    def codigo_receita_agt_formatado(self, obj):
        return format_html(
            '<span style="background-color: #1e3a8a; color: white; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-weight: bold;">{}</span>',
            obj.codigo_receita_agt
        )
    codigo_receita_agt_formatado.short_description = 'Código AGT'
    codigo_receita_agt_formatado.admin_order_field = 'codigo_receita_agt'
    
    def nome_imposto_curto(self, obj):
        nome = obj.nome
        if len(nome) > 40:
            return f"{nome[:40]}..."
        return nome
    nome_imposto_curto.short_description = 'Imposto'
    nome_imposto_curto.admin_order_field = 'nome'
    
    def periodo_referencia(self, obj):
        return f"{obj.mes_referencia:02d}/{obj.ano_referencia}"
    periodo_referencia.short_description = 'Período'
    periodo_referencia.admin_order_field = 'ano_referencia'
    
    def regime_tributario_badge(self, obj):
        cores = {
            'geral': '#10b981',
            'simplificado': '#3b82f6',
            'iva_geral': '#8b5cf6',
            'iva_simplificado': '#06b6d4',
            'especial_petrolifero_mineiro': '#f59e0b',
        }
        cor = cores.get(obj.regime_tributario, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            cor,
            obj.get_regime_tributario_display()[:15]
        )
    regime_tributario_badge.short_description = 'Regime'
    regime_tributario_badge.admin_order_field = 'regime_tributario'
    
    def valor_devido_formatado(self, obj):
        if obj.valor_devido > 0:
            return format_html(
                '<span style="font-weight: bold; color: #dc2626; font-family: monospace;">AOA {:,.2f}</span>',
                obj.valor_devido
            )
        return format_html('<span style="color: #6b7280; font-family: monospace;">AOA 0,00</span>')
    valor_devido_formatado.short_description = 'Valor Devido'
    valor_devido_formatado.admin_order_field = 'valor_devido'
    
    def situacao_badge(self, obj):
        cores = {
            'pendente': '#6b7280',
            'calculado': '#3b82f6',
            'declarado': '#8b5cf6',
            'pago': '#10b981',
            'parcelado': '#f59e0b',
            'vencido': '#dc2626',
            'isento': '#6b7280',
            'suspenso': '#ef4444',
        }
        cor = cores.get(obj.situacao, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            cor,
            obj.get_situacao_display()
        )
    situacao_badge.short_description = 'Situação'
    situacao_badge.admin_order_field = 'situacao'
    
    def dias_vencimento_badge(self, obj):
        try:
            dias = (obj.data_vencimento - date.today()).days
            if dias < 0:
                return format_html(
                    '<span style="background-color: #dc2626; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">Vencido {} dias</span>',
                    abs(dias)
                )
            elif dias <= 7:
                return format_html(
                    '<span style="background-color: #f59e0b; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{} dias</span>',
                    dias
                )
            else:
                return format_html(
                    '<span style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px;">{} dias</span>',
                    dias
                )
        except:
            return format_html('<span style="color: #6b7280;">-</span>')
    dias_vencimento_badge.short_description = 'Vencimento'
    
    def percentual_pago_progress(self, obj):
        try:
            if obj.total_agt > 0:
                percentual = (obj.valor_pago / obj.total_agt) * 100
            else:
                percentual = 0
                
            if percentual >= 100:
                cor = '#10b981'
            elif percentual >= 50:
                cor = '#f59e0b'
            else:
                cor = '#dc2626'
            
            return format_html(
                '''
                <div style="width: 100px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden;">
                    <div style="width: {}%; height: 20px; background-color: {}; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold;">
                        {:.0f}%
                    </div>
                </div>
                ''',
                min(percentual, 100),
                cor,
                percentual
            )
        except:
            return format_html('<span style="color: #6b7280;">0%</span>')
    percentual_pago_progress.short_description = '% Pago'
    
    def acoes_rapidas(self, obj):
        buttons = []
        
        if obj.situacao == 'pendente':
            buttons.append(
                f'<a href="#" onclick="calcularImposto({obj.pk})" style="background-color: #3b82f6; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">📊 Calcular</a>'
            )
        
        if obj.situacao in ['calculado', 'declarado'] and obj.valor_devido > 0:
            buttons.append(
                f'<a href="#" onclick="pagarImposto({obj.pk})" style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 2px;">💳 Pagar</a>'
            )
        
        return format_html(''.join(buttons))
    acoes_rapidas.short_description = 'Ações'
    
    # Actions específicas
    def calcular_impostos_selecionados(self, request, queryset):
        count = 0
        total_calculado = Decimal('0.00')
        
        for imposto in queryset:
            if imposto.situacao in ['pendente', 'calculado']:
                valor = imposto.calcular_imposto_angola(forcar_recalculo=True)
                total_calculado += valor
                count += 1
        
        if count > 0:
            self.message_user(
                request,
                f'✅ {count} impostos calculados. Total: AOA {total_calculado:,.2f}',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                '⚠️ Nenhum imposto foi calculado. Verifique a situação dos impostos selecionados.',
                messages.WARNING
            )
    calcular_impostos_selecionados.short_description = '📊 Calcular impostos selecionados'
    
    def marcar_como_pago(self, request, queryset):
        count = queryset.filter(situacao__in=['calculado', 'declarado', 'vencido']).update(
            situacao='pago',
            data_pagamento=timezone.now().date(),
            valor_pago=models.F('total_agt')
        )
        
        if count > 0:
            self.message_user(
                request,
                f'✅ {count} impostos marcados como pagos.',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                '⚠️ Nenhum imposto foi marcado como pago.',
                messages.WARNING
            )
    marcar_como_pago.short_description = '✅ Marcar como pago'

# ============================================================================
# CONFIGURAÇÃO DE IMPOSTOS
# ============================================================================

@admin.register(ConfiguracaoImposto)
class ConfiguracaoImpostoAdmin(admin.ModelAdmin):
    list_display = [
        'empresa_info',
        'regime_tributario_badge',
        'setor_atividade_badge',
        'provincia_badge',
        'iva_aplicavel_display',
        'impostos_aplicaveis_count',
        'status_configuracao'
    ]
    
    list_filter = [
        'regime_tributario_principal',
        'regime_iva',
        'setor_atividade',
        'provincia',
        'gerar_impostos_automaticamente',
        'eh_setor_petrolifero',
        'eh_setor_mineiro'
    ]
    
    search_fields = [
        'empresa__razao_social',
        'empresa__nome_fantasia',
        'observacoes'
    ]
    
    fieldsets = (
        ('🇦🇴 Empresa e Identificação', {
            'fields': (
                'empresa',
                'responsavel_fiscal',
            )
        }),
        ('🏛️ Regimes Tributários', {
            'fields': (
                ('regime_tributario_principal', 'regime_iva'),
                ('setor_atividade', 'provincia'),
                ('eh_setor_petrolifero', 'eh_setor_mineiro', 'eh_setor_diamantifero'),
            )
        }),
        ('💰 Alíquotas (%)', {
            'fields': (
                ('aliquota_iva_geral', 'aliquota_iva_simplificado'),
                'aliquota_iva_cabinda',
                ('aliquota_imposto_industrial_geral', 'aliquota_imposto_industrial_especial'),
                ('aliquota_iac_depositos', 'aliquota_iac_titulos'),
                ('aliquota_imposto_selo', 'aliquota_imposto_veiculos'),
            )
        }),
        ('🤖 Automação', {
            'fields': (
                'gerar_impostos_automaticamente',
                'dia_vencimento_impostos',
                'impostos_aplicaveis',
            )
        }),
        ('📝 Observações', {
            'fields': (
                'observacoes',
                'data_ultima_atualizacao_aliquotas',
            )
        })
    )
    
    readonly_fields = [
        'data_ultima_atualizacao_aliquotas'
    ]
    
    def empresa_info(self, obj):
        return format_html(
            '<div><strong>{}</strong><br><small>{}</small></div>',
            obj.empresa.razao_social,
            obj.empresa.nif or 'Sem NIF'
        )
    empresa_info.short_description = 'Empresa'
    
    def regime_tributario_badge(self, obj):
        return format_html(
            '<div>'
            '<span style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-right: 2px;">{}</span><br>'
            '<span style="background-color: #8b5cf6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">IVA: {}</span>'
            '</div>',
            obj.get_regime_tributario_principal_display()[:10],
            obj.get_regime_iva_display()[:10]
        )
    regime_tributario_badge.short_description = 'Regimes'
    
    def setor_atividade_badge(self, obj):
        icones = {
            'comercio': '🛒',
            'industria': '🏭',
            'servicos': '🛠️',
            'bancario': '🏦',
            'petroleo': '🛢️',
            'mineiro': '⛏️',
        }
        icone = icones.get(obj.setor_atividade, '📋')
        
        return format_html(
            '<div style="text-align: center;">'
            '<div style="font-size: 18px;">{}</div>'
            '<div style="font-size: 11px; margin-top: 2px;">{}</div>'
            '</div>',
            icone,
            obj.get_setor_atividade_display()[:12]
        )
    setor_atividade_badge.short_description = 'Setor'
    
    def provincia_badge(self, obj):
        if obj.provincia == 'cabinda':
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">'
                'CABINDA (IVA 1%)'
                '</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #4b5563; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
                obj.get_provincia_display()
            )
    provincia_badge.short_description = 'Província'
    
    def iva_aplicavel_display(self, obj):
        aliquota = obj.get_aliquota_iva_aplicavel()
        cor = '#dc2626' if obj.provincia == 'cabinda' else '#3b82f6'
        
        return format_html(
            '<div style="text-align: center; font-weight: bold; color: {};">'
            '{}%<br><small style="color: #666;">IVA</small>'
            '</div>',
            cor,
            aliquota
        )
    iva_aplicavel_display.short_description = 'IVA Aplicável'
    
    def impostos_aplicaveis_count(self, obj):
        count = len(obj.impostos_aplicaveis) if obj.impostos_aplicaveis else 0
        return format_html(
            '<div style="text-align: center;">'
            '<span style="background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 50%; font-weight: bold;">{}</span>'
            '<br><small style="color: #666;">impostos</small>'
            '</div>',
            count
        )
    impostos_aplicaveis_count.short_description = 'Qtd Impostos'
    
    def status_configuracao(self, obj):
        issues = []
        
        if not obj.impostos_aplicaveis:
            issues.append("Sem impostos")
        
        if obj.get_aliquota_iva_aplicavel() == 0:
            issues.append("IVA zerado")
        
        if not issues:
            return format_html('<span style="color: #10b981; font-weight: bold;">✅ Completa</span>')
        else:
            return format_html(
                '<span style="color: #dc2626; font-weight: bold;" title="{}">⚠️ Pendências</span>',
                ' | '.join(issues)
            )
    status_configuracao.short_description = 'Status'

# ============================================================================
# REGISTROS ADICIONAIS SIMPLIFICADOS
# ============================================================================

@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_dre', 'descricao']
    list_filter = ['tipo_dre']
    search_fields = ['nome', 'descricao']

@admin.register(ContaPai)
class ContaPaiAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'descricao', 'valor_original', 'valor_saldo', 'status', 'data_vencimento']
    list_filter = ['status', 'data_vencimento']
    search_fields = ['numero_documento', 'descricao']

@admin.register(FluxoCaixa)
class FluxoCaixaAdmin(admin.ModelAdmin):
    list_display = ['data_referencia', 'tipo', 'categoria', 'valor_previsto', 'valor_realizado', 'realizado']
    list_filter = ['tipo', 'realizado', 'data_referencia']
    search_fields = ['categoria', 'descricao']

@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    list_display = ['conta_bancaria', 'data_inicio', 'data_fim', 'saldo_banco_final', 'saldo_sistema_final', 'diferenca', 'status']
    list_filter = ['status', 'conta_bancaria']

@admin.register(OrcamentoFinanceiro)
class OrcamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['ano', 'mes', 'tipo', 'plano_contas', 'valor_orcado', 'valor_realizado', 'percentual_realizacao']
    list_filter = ['ano', 'mes', 'tipo']

@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['numero_lancamento', 'data_lancamento', 'tipo', 'valor', 'plano_contas', 'descricao']
    list_filter = ['tipo', 'data_lancamento']
    search_fields = ['numero_lancamento', 'descricao']
    
