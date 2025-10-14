# Em apps/core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import Empresa, Loja, Usuario, Categoria
from apps.licenca.models import Licenca 

# =============================================================================
# DEFINIÇÃO DOS INLINES (AQUI, NO MESMO FICHEIRO)
# =============================================================================

class LojaInline(admin.TabularInline):
    model = Loja
    extra = 0


class LicencaInline(admin.TabularInline):
    model = Licenca
    extra = 0


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Interface de administração para o modelo Categoria.
    """
    
    # Campos a serem exibidos na lista
    list_display = (
        'nome', 
        'empresa',
        'codigo', 
        'ativa'
    )
    
    # Campos que podem ser editados diretamente na lista
    list_editable = (
        'ativa',
    )
    
    # Opções de filtro na barra lateral
    list_filter = (
        'ativa', 
        'empresa' # Essencial para sistemas multi-empresa
    )
    
    # Campos pelos quais se pode pesquisar
    search_fields = (
        'nome', 
        'codigo', 
        'empresa__nome' # Permite pesquisar pelo nome da empresa
    )
    
    # Otimiza a seleção de 'empresa' se houver muitas
    autocomplete_fields = (
        'empresa',
    )

    # Organização do formulário de edição/criação
    fieldsets = (
        (None, {
            'fields': ('empresa', ('nome', 'codigo'), 'ativa')
        }),
        ('Detalhes Adicionais', {
            'classes': ('collapse',),
            'fields': ('descricao',)
        }),
    )


# =============================================================================
# ADMINS DOS MODELOS
# =============================================================================

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nif', 'cidade', 'status_licenca', 'ativa', 'total_usuarios']
    list_filter = ['ativa', 'provincia', 'licenca__status', 'licenca__plano']
    search_fields = ['nome', 'nif', 'cidade']
    
    # Use os inlines definidos localmente
    inlines = [LicencaInline, LojaInline]
    
    # O resto do seu código EmpresaAdmin está excelente e pode ser mantido aqui
    # ... (fieldsets, status_licenca, total_usuarios, actions, etc.) ...
    fieldsets = (
        ('Dados Básicos', {'fields': ('nome', 'nome_fantasia', 'nif')}),
        ('Endereço', {'fields': (('endereco', 'numero'), ('bairro', 'cidade'), ('provincia', 'postal'))}),
        ('Contato', {'fields': ('telefone', 'email')}),
        ('Status', {'fields': ('ativa',)}),
    )
    actions = ['ativar_empresas', 'desativar_empresas']

    def status_licenca(self, obj):
        # ... seu código aqui ...
        return "Status" # Placeholder
    status_licenca.short_description = 'Status da Licença'

    def total_usuarios(self, obj):
        # ... seu código aqui ...
        return "0/0" # Placeholder
    total_usuarios.short_description = 'Usuários (Atual/Limite)'

    def ativar_empresas(self, request, queryset):
        count = queryset.update(ativa=True)
        self.message_user(request, f'{count} empresas ativadas.')
    ativar_empresas.short_description = "Ativar empresas selecionadas"

    def desativar_empresas(self, request, queryset):
        count = queryset.update(ativa=False)
        self.message_user(request, f'{count} empresas desativadas.')
    desativar_empresas.short_description = "Desativar empresas selecionadas"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Define a interface de administração para o modelo de Utilizador personalizado.
    """
    # 1. CAMPOS A EXIBIR NA LISTA DE UTILIZADORES
    # Adicionamos 'empresa' e 'e_administrador_empresa' à lista.
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'empresa', 
        'e_administrador_empresa', 
        'is_staff'
    )

    # 2. FILTROS DA BARRA LATERAL
    # Adicionamos 'empresa' como uma opção de filtro.
    list_filter = ('is_staff', 'is_superuser', 'groups', 'empresa')

    search_fields = ('username', 'first_name', 'last_name', 'email', 'empresa__nome')
    
    fieldsets = (

        *UserAdmin.fieldsets,

        ('Perfil Profissional e Vínculos', {
            'fields': (
                'empresa', 
                'loja', 
                'telefone', 
                'e_administrador_empresa'
            ),
        }),
    )


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'codigo', 'cidade', 'eh_matriz', 'ativa']
    list_filter = ['ativa', 'eh_matriz', 'empresa']
    search_fields = ['nome', 'codigo', 'cidade']  # ✅ OBRIGATÓRIO para autocomplete
