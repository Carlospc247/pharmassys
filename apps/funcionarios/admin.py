# apps/funcionarios/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.contrib import messages
from django.contrib.auth.models import User
from .models import (
    Cargo, Departamento, Funcionario, EscalaTrabalho,
    RegistroPonto, Capacitacao, AvaliacaoDesempenho
)

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.models import Permission
from .models import Cargo, Departamento, Funcionario


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'categoria', 'nivel_hierarquico', 'salario_base',
        'funcionarios_ativos_count', 'ativo'
    ]
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'codigo', 'descricao']
    list_editable = ['ativo']

    # --- Adicionado: interface de permissões visuais ---
    filter_horizontal = ['permissions']

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'codigo', 'descricao')
        }),
        ('Hierarquia', {
            'fields': ('cargo_superior', 'nivel_hierarquico', 'categoria')
        }),
        ('Remuneração', {
            'fields': ('salario_base', 'vale_alimentacao', 'vale_transporte', "pode_pagar_salario")
        }),
        ('Permissões gerais', {
            'fields': ('selecionar_todos',),
            'description': "Marque para selecionar ou desmarcar todas as permissões abaixo."
        }),
        ('Permissões de Vendas', {
            'fields': ('pode_vender', 'pode_fazer_desconto', 'limite_desconto_percentual',
                    'pode_cancelar_venda', 'pode_fazer_devolucao', 'pode_alterar_preco')
        }),
        ('Permissões de Gestão', {
            'fields': ('pode_gerenciar_estoque', 'pode_fazer_compras', 'pode_aprovar_pedidos',
                    'pode_gerenciar_funcionarios', 'pode_ver_vendas', "pode_editar_produtos")
        }),
        ('Permissões de Gestão interna', {
            'fields': ('pode_acessar_financeiro', 'pode_acessar_rh', 'pode_acessar_fornecedores',)
        }),
        ('Permissões de Faturas', {
            'fields': (
                'pode_emitir_faturacredito',
                'pode_liquidar_faturacredito',
                'pode_emitir_proforma',
                'pode_aprovar_proforma',
                'pode_emitir_recibo',
                'pode_acessar_documentos',
            )
        }),
        ('Permissões fiscais', {
            'fields': (
                'pode_emitir_notacredito',
                'pode_aplicar_notacredito',
                'pode_aprovar_notacredito',
                'pode_emitir_notadebito',
                'pode_aplicar_notadebito',
                'pode_aprovar_notadebito',
                'pode_emitir_documentotransporte',
                'pode_confirmar_entrega',
            )
        }),
        ('Permissões de configurações e fiscal', {
            'fields': (
                'pode_acessar_configuracoes',
                'pode_alterar_dados_fiscais',
                'pode_eliminar_detalhes_fiscal',
                'pode_acessar_detalhes_fiscal',
                'pode_atualizar_backups',
                'pode_ver_configuracoes',
                'pode_alterar_interface',
            )
        }),
        ('Permissões de SAFT e fiscal', {
            'fields': (
                'pode_exportar_saft',
                'pode_ver_historico_saft',
                'pode_baixar_saft',
                'pode_validar_saft',
                'pode_visualizar_saft',
                'pode_ver_status_saft',
                'pode_criar_dados_bancarios',
                'pode_apagar_dados_bancarios',
                'pode_atualizar_dados_bancarios',
                'pode_ver_taxaiva_agt',
                'pode_gerir_assinatura_digital',
                'pode_gerir_retencoes_na_fonte',
                'pode_criar_retencoes_na_fonte',
                'pode_apagar_retencoes_na_fonte',
                'pode_acessar_dashboard_fiscal',
                'pode_validar_documentos_fiscais',
                'pode_verificar_integridade_hash',
                'pode_acessar_painel_principal_fiscal',
                'pode_ver_taxas_iva',
                'pode_criar_taxas_iva',
                'pode_apagar_taxas_iva',
                'pode_ver_status_atual_assinatura_digital',
                'pode_configurar_assinatura_digital',
                'pode_gerar_par_chave_publica_ou_privada',
            )
        }),
        ('Permissões de SAFT e relatórios', {
            'fields': (
                'pode_ver_relatorio_fiscal',
                'pode_ver_relatorio_retencoes',
                'pode_ver_relatorio_taxas_iva',
                'pode_acessar_dashboard_saft',
                'pode_baixar_chave_publica',
                'pode_baixar_retencoes',
                'pode_baixar_saft_backup_fiscal',
                'pode_baixar_relatorio_retencoes',
                'pode_acessar_configuracao_fiscal',
                'pode_verificar_integridade_cadeia_hash_fiscal',
            )
        }),
        ('Permissões do Sistema (Django)', {
            'fields': ('permissions',),
            'description': "Permissões nativas do Django aplicáveis a este cargo. "
                        "Essas permissões também serão atribuídas ao grupo correspondente."
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

    

    def funcionarios_ativos_count(self, obj):
        count = obj.funcionarios_ativos
        if count > 0:
            url = reverse('admin:funcionarios_funcionario_changelist') + f'?cargo__id__exact={obj.id}&ativo__exact=1'
            return format_html('<a href="{}">{} funcionários</a>', url, count)
        return '0 funcionários'

    funcionarios_ativos_count.short_description = 'Funcionários'


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'loja', 'responsavel', 'funcionarios_count', 'ativo']
    list_filter = ['loja', 'ativo']
    search_fields = ['nome', 'codigo', 'descricao']

    def funcionarios_count(self, obj):
        count = obj.funcionarios.filter(ativo=True).count()
        if count > 0:
            url = reverse('admin:funcionarios_funcionario_changelist') + f'?departamento__id__exact={obj.id}'
            return format_html('<a href="{}">{} funcionários</a>', url, count)
        return '0 funcionários'

    funcionarios_count.short_description = 'Funcionários'


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    readonly_fields = ("matricula",)

    list_display = (
        "nome_completo", "cargo", "departamento",
        "loja_principal", "ativo", "data_admissao", "data_demissao"
    )
    list_filter = (
        "ativo", "departamento", "cargo", "loja_principal",
        "tipo_contrato", "escolaridade", "estado_civil"
    )
    search_fields = (
        "matricula", "nome_completo", "bi", "email_pessoal", "email_corporativo"
    )
    ordering = ("nome_completo",)
    autocomplete_fields = ("usuario", "cargo", "departamento", "loja_principal", "supervisor", "empresa")
    filter_horizontal = ("lojas_acesso",)

    fieldsets = (
        ("Identificação", {
            "fields": ("matricula", "usuario", "empresa")
        }),
        ("Dados Pessoais", {
            "fields": (
                "nome_completo", "bi", "data_nascimento", "sexo",
                "estado_civil", "nacionalidade", "naturalidade"
            )
        }),
        ("Endereço", {
            "fields": ("endereco", "numero", "bairro", "cidade", "provincia", "postal")
        }),
        ("Contato", {
            "fields": ("telefone", "whatsapp", "email_pessoal", "email_corporativo")
        }),
        ("Profissional", {
            "fields": ("cargo", "departamento", "loja_principal", "lojas_acesso", "supervisor")
        }),
        ("Contrato", {
            "fields": (
                "tipo_contrato", "data_admissao", "data_demissao",
                "periodo_experiencia_dias", "data_fim_experiencia"
            )
        }),
        ("Remuneração", {
            "fields": (
                "salario_atual", "vale_alimentacao", "vale_transporte",
                "outros_beneficios", "comissao_percentual"
            )
        }),
        ("Formação", {
            "fields": ("escolaridade", "curso_formacao", "instituicao_ensino", "ano_conclusao")
        }),
        ("Registros Profissionais", {
            "fields": ( "outros_registros",)
        }),
        ("Bancário", {
            "fields": ("banco", "agencia", "conta_corrente", "tipo_conta")
        }),
        ("Jornada de Trabalho", {
            "fields": (
                "carga_horaria_semanal", "horario_entrada", "horario_saida",
                "horario_almoco_inicio", "horario_almoco_fim",
                "trabalha_sabado", "trabalha_domingo", "trabalha_feriado"
            )
        }),
        ("Status", {
            "fields": (
                "ativo", "em_experiencia", "afastado", "motivo_afastamento",
                "data_inicio_afastamento", "data_fim_afastamento"
            )
        }),
        ("Observações", {
            "fields": ("observacoes", "observacoes_rh")
        }),
        ("Foto", {
            "fields": ("foto",)
        }),
    )


@admin.register(EscalaTrabalho)
class EscalaTrabalhoAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'data_trabalho', 'turno', 'loja',
        'horario_entrada', 'horario_saida', 'horas_trabalhadas_display',
        'confirmada', 'trabalhada'
    ]
    list_filter = ['turno', 'loja', 'confirmada', 'trabalhada', 'data_trabalho']
    search_fields = ['funcionario__nome_completo', 'funcionario__matricula']
    date_hierarchy = 'data_trabalho'
    
    def horas_trabalhadas_display(self, obj):
        horas = obj.horas_trabalhadas
        return f"{horas:.1f}h"
    horas_trabalhadas_display.short_description = 'Horas'

@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'data_registro', 'hora_registro', 'tipo_registro',
        'loja', 'registro_manual', 'aprovado_por'
    ]
    list_filter = ['tipo_registro', 'loja', 'registro_manual', 'data_registro']
    search_fields = ['funcionario__nome_completo', 'funcionario__matricula']
    date_hierarchy = 'data_registro'


@admin.register(Capacitacao)
class CapacitacaoAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'titulo', 'tipo', 'data_inicio', 'data_fim',
        'carga_horaria', 'total_display', 'status'
    ]
    list_filter = ['tipo', 'status', 'modalidade', 'data_inicio']
    search_fields = ['funcionario__nome_completo', 'titulo', 'instituicao']
    readonly_fields = ['total']
    
    def total_display(self, obj):
        return format_html('R$ {:.2f}', obj.total)
    total_display.short_description = 'Valor Total'

@admin.register(AvaliacaoDesempenho)
class AvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'tipo_avaliacao', 'data_avaliacao', 'avaliador',
        'nota_geral_display', 'recomenda_promocao', 'recomenda_aumento'
    ]
    list_filter = ['tipo_avaliacao', 'data_avaliacao', 'avaliador', 'recomenda_promocao', 'recomenda_aumento']
    search_fields = ['funcionario__nome_completo', 'funcionario__matricula']
    readonly_fields = ['nota_geral']
    
    fieldsets = (
        ('Avaliação', {
            'fields': ('funcionario', 'tipo_avaliacao', 'periodo_inicio', 'periodo_fim', 'data_avaliacao', 'avaliador')
        }),
        ('Critérios de Avaliação', {
            'fields': ('pontualidade', 'assiduidade', 'qualidade_trabalho', 'produtividade', 'iniciativa', 'relacionamento_interpessoal', 'conhecimento_tecnico', 'lideranca')
        }),
        ('Resultado', {
            'fields': ('nota_geral',)
        }),
        ('Comentários', {
            'fields': ('pontos_fortes', 'pontos_melhorar', 'metas_objetivos', 'plano_desenvolvimento')
        }),
        ('Recomendações', {
            'fields': ('recomenda_promocao', 'recomenda_aumento', 'recomenda_capacitacao')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    def nota_geral_display(self, obj):
        if obj.nota_geral:
            if obj.nota_geral >= 4.5:
                color = 'green'
            elif obj.nota_geral >= 3.5:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
                color, obj.nota_geral
            )
        return '-'
    nota_geral_display.short_description = 'Nota Geral'

