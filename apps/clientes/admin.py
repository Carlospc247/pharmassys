# apps/clientes/admin.py
from django.contrib import admin
from .models import (
    Cliente, Ponto, CategoriaCliente, EnderecoCliente,
    ContatoCliente, HistoricoCliente,
    CartaoFidelidade, MovimentacaoFidelidade, PreferenciaCliente,
    TelefoneCliente, GrupoCliente, ProgramaFidelidade
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    search_fields = ("nome_completo", "nome_social", "bi", "nif", "email", "telefone")
    list_filter = ("tipo_cliente", "sexo", "ativo", "bloqueado", "vip", "categoria_cliente")
    list_display = ("codigo_cliente", "nome_exibicao", "tipo_cliente", "ativo", "vip", "empresa")
   

@admin.register(Ponto)
class PontoAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo",)
    list_display = ("cliente", "valor", "data")
   

@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    list_display = ("nome", "desconto_padrao", "limite_credito_padrao", "ativa")

@admin.register(EnderecoCliente)
class EnderecoClienteAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo", "cidade", "bairro")
    list_filter = ("tipo_endereco", "endereco_principal", "endereco_entrega")
    list_display = ("cliente", "nome_endereco", "tipo_endereco", "cidade", "provincia", "ativo")
  

@admin.register(ContatoCliente)
class ContatoClienteAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo", "valor_contato")
    list_filter = ("tipo_contato", "contato_principal", "ativo")
    list_display = ("cliente", "tipo_contato", "valor_contato", "contato_principal", "ativo")
    
   

@admin.register(HistoricoCliente)
class HistoricoClienteAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo", "titulo")
    list_filter = ("tipo_interacao", "prioridade", "resolvido")
    list_display = ("cliente", "tipo_interacao", "titulo", "usuario_responsavel", "data_interacao")
    

@admin.register(CartaoFidelidade)
class CartaoFidelidadeAdmin(admin.ModelAdmin):
    search_fields = ("numero_cartao", "cliente__nome_completo")
    list_display = ("numero_cartao", "cliente", "pontos_atuais", "nivel_atual", "ativo")
   

@admin.register(MovimentacaoFidelidade)
class MovimentacaoFidelidadeAdmin(admin.ModelAdmin):
    search_fields = ("cartao__numero_cartao", "cartao__cliente__nome_completo")
    list_filter = ("tipo_movimentacao",)
    list_display = ("cartao", "tipo_movimentacao", "pontos", "descricao", "data_movimentacao")
    

@admin.register(PreferenciaCliente)
class PreferenciaClienteAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo",)
    list_display = ("cliente", "produto", "categoria", "fabricante", "prioridade", "ativa")
    

@admin.register(TelefoneCliente)
class TelefoneClienteAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo", "numero")
    list_display = ("cliente", "numero", "tipo", "created_at")
    

@admin.register(GrupoCliente)
class GrupoClienteAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    list_display = ("nome", "desconto_padrao", "empresa")
    

@admin.register(ProgramaFidelidade)
class ProgramaFidelidadeAdmin(admin.ModelAdmin):
    search_fields = ("cliente__nome_completo",)
    list_display = ("cliente", "pontos", "nivel", "data_entrada")
   


