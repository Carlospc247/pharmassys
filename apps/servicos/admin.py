# apps/servicos/admin.py
from pyexpat.errors import messages
from django.contrib import admin
from django.utils.html import format_html
from .models import Servico, AgendamentoServico, NotificacaoAgendamento, ConfiguracaoNotificacao




from django.contrib import admin
from .models import Servico, AgendamentoServico


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nome",
        "empresa",
        "categoria",
        "duracao_padrao_minutos",
        "preco_padrao",
        "ativo",
    )
    list_filter = ("empresa", "categoria", "ativo")
    search_fields = ("nome", "empresa__nome")
    ordering = ("nome",)
    list_editable = ("ativo",)
    fieldsets = (
        (None, {
            "fields": (
                "empresa",
                "nome",
                "categoria",
                "duracao_padrao_minutos",
                "preco_padrao",
                "instrucoes_padrao",
                "ativo",
            )
        }),
    )


@admin.register(AgendamentoServico)
class AgendamentoServicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "servico",
        "cliente",
        "funcionario",
        "empresa",
        "data_hora",
        "status",
        "valor_cobrado",
    )
    list_filter = ("empresa", "status", "funcionario", "servico")
    search_fields = (
        "servico__nome",
        "cliente__nome_completo",
        "funcionario__nome_completo",
        "empresa__nome",
    )
    ordering = ("-data_hora",)
    date_hierarchy = "data_hora"
    fieldsets = (
        ("Informações principais", {
            "fields": (
                "empresa",
                "servico",
                "cliente",
                "funcionario",
                "status",
                "data_hora",
                "valor_cobrado",
            )
        }),
        ("Execução", {
            "fields": (
                "data_inicio_real",
                "data_fim_real",
                "resultado",
            ),
            "classes": ("collapse",),
        }),
        ("Observações", {
            "fields": ("observacoes",),
            "classes": ("collapse",),
        }),
    )




######################
@admin.register(NotificacaoAgendamento)
class NotificacaoAgendamentoAdmin(admin.ModelAdmin):
    """
    Interface de administração avançada para o modelo de Notificações de Agendamento.
    """
    # --- Ações em Massa ---
    actions = ['reenviar_notificacoes_pendentes_ou_com_erro']

    # --- Configuração da Lista ---
    list_display = (
        'agendamento',
        'cliente',
        'tipo_notificacao',
        'data_agendada_envio',
        'status',
        'empresa',
    )
    list_filter = ('status', 'tipo_notificacao', 'data_agendada_envio', 'empresa')
    search_fields = ('cliente__nome_completo', 'titulo', 'agendamento__servico__nome')
    date_hierarchy = 'data_agendada_envio'

    # --- Configuração do Formulário de Edição/Criação ---
    autocomplete_fields = ('agendamento', 'cliente', 'empresa')
    
    # Campos que são logs e não devem ser editados manualmente
    readonly_fields = (
        'data_envio',
        'data_entrega',
        'data_leitura',
        'tentativas_envio',
        'erro_envio',
        'email_enviado',
        'telefone_enviado',
    )
    
    fieldsets = (
        ('Associação', {
            'fields': ('empresa', 'agendamento', 'cliente')
        }),
        ('Configuração do Envio', {
            'fields': ('tipo_notificacao', 'data_agendada_envio', 'dias_antecedencia')
        }),
        ('Conteúdo da Mensagem', {
            'fields': ('titulo', 'mensagem')
        }),
        ('Logs de Envio (Automático)', {
            'description': 'Estes campos são preenchidos automaticamente pelo sistema.',
            'classes': ('collapse',),
            'fields': readonly_fields
        }),
    )

    # --- Ações Personalizadas ---
    @admin.action(description="Reenviar notificações pendentes ou com erro")
    def reenviar_notificacoes_pendentes_ou_com_erro(self, request, queryset):
        """
        Permite selecionar notificações e tentar reenviá-las se estiverem
        nos status 'pendente' ou 'erro'.
        """
        sucesso = 0
        falha = 0
        queryset_para_envio = queryset.filter(status__in=['pendente', 'erro'])
        
        for notificacao in queryset_para_envio:
            if notificacao.enviar_notificacao():
                sucesso += 1
            else:
                falha += 1
        
        if sucesso > 0:
            self.message_user(request, f'{sucesso} notificações foram adicionadas à fila de envio.', messages.SUCCESS)
        if falha > 0:
            self.message_user(request, f'{falha} notificações falharam ao ser reenviadas. Verifique os logs.', messages.ERROR)
        if sucesso == 0 and falha == 0:
             self.message_user(request, 'Nenhuma notificação selecionada estava apta para reenvio (status "pendente" ou "erro").', messages.WARNING)

@admin.register(ConfiguracaoNotificacao)
class ConfiguracaoNotificacaoAdmin(admin.ModelAdmin):
    list_display = (
        'empresa',
        'email_ativo',
        'sms_ativo',
        'whatsapp_ativo',
        'dias_notificacao',
        'horario_inicio_envio',
        'horario_fim_envio',
    )
    list_filter = (
        'email_ativo',
        'sms_ativo',
        'whatsapp_ativo',
    )
    search_fields = ('empresa__nome',)
    autocomplete_fields = ['empresa']
    fieldsets = (
        ("Empresa", {
            'fields': ('empresa',)
        }),
        ("Ativação", {
            'fields': ('email_ativo', 'sms_ativo', 'whatsapp_ativo')
        }),
        ("Configuração de Prazos", {
            'fields': ('dias_notificacao', 'horario_inicio_envio', 'horario_fim_envio')
        }),
        ("Templates de Mensagem", {
            'fields': ('template_email_titulo', 'template_email_mensagem', 'template_sms_mensagem')
        }),
        ("Configurações Avançadas", {
            'fields': ('max_tentativas_envio', 'intervalo_tentativas_horas')
        }),
    )





