# apps/configuracoes/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    ConfiguracaoFiscal,
 BackupConfiguracao,
    HistoricoBackup, PersonalizacaoInterface
)

import os
from django.template.defaultfilters import filesizeformat


@admin.register(ConfiguracaoFiscal)
class ConfiguracaoFiscalAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'razao_social', 'nif', 'regime_tributario'
    ]
    list_filter = ['regime_tributario', 'provincia']
    search_fields = ['razao_social', 'nif', 'empresa__nome']

    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa', 'razao_social', 'nome_fantasia', 'nif')
        }),
        ('Endereço Fiscal', {
            'fields': ('endereco', 'cidade', 'provincia', 'postal')
        }),
        ('Regime Tributário', {
            'fields': ('regime_tributario',)
        }),
        ('Impressão', {
            'fields': ('impressora_cupom',),
            'classes': ['collapse']
        }),
        
    )
    
    def certificado_status(self, obj):
        if not obj.certificado_arquivo:
            return format_html('<span style="color: red;">Não configurado</span>')
        elif obj.certificado_vencido:
            return format_html('<span style="color: red;">Vencido</span>')
        else:
            return format_html('<span style="color: green;">Válido</span>')
    certificado_status.short_description = 'Certificado'


@admin.register(BackupConfiguracao)
class BackupConfiguracaoAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'backup_automatico', 'frequencia_backup', 'horario_backup',
        'ultimo_backup', 'status_ultimo_backup_display'
    ]
    list_filter = ['backup_automatico', 'frequencia_backup']
    readonly_fields = ['ultimo_backup', 'status_ultimo_backup']
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Configurações de Backup', {
            'fields': ('backup_automatico', 'frequencia_backup', 'horario_backup')
        }),
        ('Retenção', {
            'fields': ('dias_retencao_backup', 'quantidade_maxima_backups')
        }),
        ('Backup Local', {
            'fields': ('backup_local', 'caminho_backup_local')
        }),
        ('Backup em Nuvem', {
            'fields': ('backup_nuvem', 'provedor_nuvem', 'configuracoes_nuvem'),
            'classes': ['collapse']
        }),
        ('Notificações', {
            'fields': ('notificar_sucesso', 'notificar_erro', 'email_notificacao'),
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ('ultimo_backup', 'status_ultimo_backup')
        }),
    )
    
    def status_ultimo_backup_display(self, obj):
        if not obj.status_ultimo_backup:
            return '-'
        
        colors = {
            'sucesso': 'green',
            'erro': 'red',
            'em_andamento': 'orange'
        }
        color = colors.get(obj.status_ultimo_backup, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_ultimo_backup_display()
        )
    status_ultimo_backup_display.short_description = 'Status Último Backup'

@admin.register(PersonalizacaoInterface)
class PersonalizacaoInterfaceAdmin(admin.ModelAdmin):
    list_display = [
        'get_nome', 'tema', 'cor_primaria_display',
        'empresa', 'usuario'
    ]
    list_filter = ['tema', 'empresa']
    search_fields = ['empresa__nome', 'usuario__username']
    
    fieldsets = (
        ('Escopo', {
            'fields': ('empresa', 'usuario')
        }),
        ('Tema e Cores', {
            'fields': ('tema', 'cor_primaria', 'cor_secundaria')
        }),
        ('Logo e Identidade', {
            'fields': ('logo_principal', 'logo_pequeno', 'favicon'),
            'classes': ['collapse']
        }),
        ('Preferências', {
            'fields': ('itens_por_pagina', 'formato_data', 'formato_moeda')
        }),
        ('Notificações', {
            'fields': ('notificacoes_browser', 'notificacoes_som'),
            'classes': ['collapse']
        }),
        ('Dashboard', {
            'fields': ('widgets_dashboard', 'layout_dashboard'),
            'classes': ['collapse']
        }),
        ('Extras', {
            'fields': ('configuracoes_extras',),
            'classes': ['collapse']
        }),
    )
    
    def get_nome(self, obj):
        if obj.usuario:
            return f"Usuário: {obj.usuario.username}"
        elif obj.empresa:
            return f"Empresa: {obj.empresa.nome}"
        else:
            return "Global"
    get_nome.short_description = 'Personalização'
    
    def cor_primaria_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.cor_primaria, obj.cor_primaria
        )
    cor_primaria_display.short_description = 'Cor Primária'



@admin.register(HistoricoBackup)
class HistoricoBackupAdmin(admin.ModelAdmin):
    """
    Interface de administração avançada para o modelo HistoricoBackup.
    """
    
    # --- Configuração da Lista de Visualização ---
    
    list_display = (
        'id',
        'empresa',
        'status_colorido',
        'tipo',
        'data_criacao',
        'tamanho_formatado',
        'download_link',
        'solicitado_por',
    )
    
    list_filter = (
        'status',
        'tipo',
        'empresa',
        'data_criacao',
    )
    
    search_fields = (
        'empresa__razao_social',
        'ficheiro_backup',
    )
    
    date_hierarchy = 'data_criacao'
    
    # --- Configuração do Formulário de Edição ---
    
    readonly_fields = (
        'id',
        'empresa',
        'tipo',
        'status',
        'data_criacao',
        'data_conclusao',
        'nome_ficheiro',
        'tamanho_formatado',
        'solicitado_por',
        'detalhes_erro',
    )
    
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('id', 'empresa', 'status', 'tipo', 'solicitado_por')
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_conclusao')
        }),
        ('Ficheiro de Backup', {
            'fields': ('nome_ficheiro', 'tamanho_formatado', 'ficheiro_backup')
        }),
        ('Diagnóstico', {
            'classes': ('collapse',),
            'fields': ('detalhes_erro',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    # --- Métodos Personalizados para a Lista ---

    @admin.display(description='Status', ordering='status')
    def status_colorido(self, obj):
        if obj.status == 'sucesso':
            cor = 'green'
            texto = 'Sucesso'
        elif obj.status == 'erro':
            cor = 'red'
            texto = 'Erro'
        else:
            cor = 'orange'
            texto = 'Processando'
        return format_html('<b style="color: {};">{}</b>', cor, texto)

    @admin.display(description='Tamanho', ordering='tamanho_ficheiro')
    def tamanho_formatado(self, obj):
        if obj.tamanho_ficheiro > 0:
            return filesizeformat(obj.tamanho_ficheiro) # Esta função agora será encontrada
        return "0 Bytes"

    @admin.display(description='Ficheiro')
    def download_link(self, obj):
        if obj.ficheiro_backup and obj.status == 'sucesso':
            url = reverse('configuracoes:backup_download', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Descarregar</a>', url)
        return "Nenhum ficheiro"
