# apps/licenca/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PlanoLicenca, Licenca, HistoricoLicenca
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from apps.core.models import Usuario



@admin.register(PlanoLicenca)
class PlanoLicencaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_mensal', 'limite_usuarios', 'funcionalidades', 'ativo']
    list_filter = ['ativo', 'inclui_financeiro', 'inclui_relatorios', 'inclui_backup']
    search_fields = ['nome', 'descricao']
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('nome', 'descricao', 'preco_mensal', 'ativo')
        }),
        ('Limites', {
            'fields': ('limite_usuarios', 'limite_produtos')
        }),
        ('Funcionalidades Incluídas', {
            'fields': ('inclui_pdv', 'inclui_estoque', 'inclui_financeiro', 
                      'inclui_relatorios', 'inclui_backup')
        }),
    )
    
    def funcionalidades(self, obj):
        """Mostrar funcionalidades do plano"""
        funcionalidades = []
        if obj.inclui_pdv: funcionalidades.append('PDV')
        if obj.inclui_estoque: funcionalidades.append('Estoque')
        if obj.inclui_financeiro: funcionalidades.append('Financeiro')
        if obj.inclui_relatorios: funcionalidades.append('Relatórios')
        if obj.inclui_backup: funcionalidades.append('Backup')
        
        return ', '.join(funcionalidades) if funcionalidades else 'Básico'
    funcionalidades.short_description = 'Funcionalidades'



    def dias_restantes(self, obj):
        """Mostrar dias restantes com cores"""
        dias = obj.dias_para_vencer
        if dias < 0:
            return format_html('<span style="color: red; font-weight: bold;">Vencida há {} dias</span>', abs(dias))
        elif dias <= 7:
            return format_html('<span style="color: orange; font-weight: bold;">{} dias</span>', dias)
        elif dias <= 30:
            return format_html('<span style="color: blue;">{} dias</span>', dias)
        else:
            return format_html('<span style="color: green;">{} dias</span>', dias)
    dias_restantes.short_description = 'Dias Restantes'
    dias_restantes.admin_order_field = 'data_vencimento'
    
    def acoes_rapidas(self, obj):
        """Botões de ação rápida"""
        botoes = []
        
        if obj.status == 'ativa' and obj.dias_para_vencer <= 30:
            botoes.append(
                f'<a class="button" href="javascript:void(0)" '
                f'onclick="renovarLicenca({obj.pk})">Renovar</a>'
            )
        
        if obj.status != 'suspensa':
            botoes.append(
                f'<a class="button" href="javascript:void(0)" '
                f'onclick="suspenderLicenca({obj.pk})">Suspender</a>'
            )
        
        return mark_safe(' '.join(botoes)) if botoes else '-'
    acoes_rapidas.short_description = 'Ações'
    
    # Ações em lote
    actions = ['renovar_licencas_1mes', 'renovar_licencas_3meses', 'suspender_licencas']
    
    def renovar_licencas_1mes(self, request, queryset):
        """Renovar licenças por 1 mês"""
        count = 0
        for licenca in queryset:
            licenca.renovar(meses=1)
            count += 1
        self.message_user(request, f"{count} licenças renovadas por 1 mês.")
    renovar_licencas_1mes.short_description = "Renovar licenças por 1 mês"
    
    def renovar_licencas_3meses(self, request, queryset):
        """Renovar licenças por 3 meses"""
        count = 0
        for licenca in queryset:
            licenca.renovar(meses=3)
            count += 1
        self.message_user(request, f"{count} licenças renovadas por 3 meses.")
    renovar_licencas_3meses.short_description = "Renovar licenças por 3 meses"
    
    def suspender_licencas(self, request, queryset):
        """Suspender licenças selecionadas"""
        count = queryset.update(status='suspensa')
        self.message_user(request, f"{count} licenças suspensas.")
    suspender_licencas.short_description = "Suspender licenças selecionadas"

@admin.register(HistoricoLicenca)
class HistoricoLicencaAdmin(admin.ModelAdmin):
    list_display = ['licenca', 'acao', 'data_anterior', 'data_nova', 'observacoes']
    list_filter = ['acao', 'created_at']
    search_fields = ['licenca__empresa__nome', 'acao', 'observacoes']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False  # Histórico é criado automaticamente





class LicencaInline(admin.StackedInline):
    """Inline para mostrar licença da empresa"""
    model = Licenca
    extra = 0
    max_num = 1
    can_delete = False
    
    fields = (
        'chave_licenca',
        ('plano', 'status'),
        ('data_inicio', 'data_vencimento'),
        'observacoes_admin'
    )
    
    readonly_fields = ('chave_licenca', 'observacoes_admin')
    
    def observacoes_admin(self, obj):
        """Campo customizado com informações da licença"""
        if not obj.pk:
            return "Licença será criada após salvar"
        
        dias = obj.dias_para_vencer
        if dias < 0:
            status_cor = 'red'
            status_texto = f'Vencida há {abs(dias)} dias'
        elif dias <= 7:
            status_cor = 'orange'
            status_texto = f'Vence em {dias} dias - ATENÇÃO!'
        elif dias <= 30:
            status_cor = 'blue'
            status_texto = f'Vence em {dias} dias'
        else:
            status_cor = 'green'
            status_texto = f'Vence em {dias} dias'
        
        return format_html(
            '<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            '<strong>Status:</strong> <span style="color: {};">{}</span><br>'
            '<strong>Usuários Permitidos:</strong> {} usuários<br>'
            '<strong>Chave:</strong> <code>{}</code><br>'
            '<strong>Criada em:</strong> {}<br>'
            '<strong>Última Atualização:</strong> {}'
            '</div>',
            status_cor,
            status_texto,
            obj.plano.limite_usuarios if obj.plano else 'N/A',
            str(obj.chave_licenca)[:8] + '...' if obj.chave_licenca else 'N/A',
            obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else 'N/A',
            obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else 'N/A'
        )
    observacoes_admin.short_description = 'Informações da Licença'



class PerfilUsuarioInline(admin.StackedInline):
    """Inline para perfil do usuário"""
    model = Usuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('empresa', 'loja', 'cargo', 'telefone')
        }),
        ('Permissões', {
            'fields': (
                'pode_vender',
                'pode_gerenciar_estoque', 
                'pode_ver_financeiro',
                'e_administrador'
            )
        }),
    )

