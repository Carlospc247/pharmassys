# apps/produtos/serializers.py
from rest_framework import serializers
from .models import Categoria, Fabricante, PrincipioAtivo, Produto, Lote, ComposicaoProduto

class CategoriaSerializer(serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()
    caminho_completo = serializers.ReadOnlyField()
    
    class Meta:
        model = Categoria
        fields = [
            'id', 'nome', 'codigo', 'descricao', 'categoria_pai',
             'icone', 'cor', 'ordem',
            'ativa', 'produtos_count', 'caminho_completo'
        ]
    
    def get_produtos_count(self, obj):
        return obj.produtos.filter(ativo=True).count()

class FabricanteSerializer(serializers.ModelSerializer):
    produtos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Fabricante
        fields = [
            'id', 'nome', 'nif', 'email', 'telefone', 'site',
            'endereco', 'cidade', 'provincia', 'cep', 'origem',
             'ativo', 'produtos_count'
        ]
    
    def get_produtos_count(self, obj):
        return obj.produtos.filter(ativo=True).count()

class PrincipioAtivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrincipioAtivo
        fields = [
            'id', 'nome', 'nome_cientifico', 'codigo_cas',
            'classe_terapeutica', 'codigo_atc',
            'lista_controle', 'ativo'
        ]


class LoteSerializer(serializers.ModelSerializer):
    dias_para_vencimento = serializers.ReadOnlyField()
    esta_vencido = serializers.ReadOnlyField()
    esta_vencendo = serializers.ReadOnlyField()
    percentual_vendido = serializers.ReadOnlyField()
    
    class Meta:
        model = Lote
        fields = [
            'id', 'numero_lote', 'data_fabricacao', 'data_vencimento',
            'quantidade_inicial', 'quantidade_atual', 'preco_custo_lote',
            'ativo', 'bloqueado', 'motivo_bloqueio', 'dias_para_vencimento',
            'esta_vencido', 'esta_vencendo', 'percentual_vendido'
        ]

class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    fabricante_nome = serializers.CharField(source='fabricante.nome', read_only=True)
    lotes = LoteSerializer(many=True, read_only=True)
    
    # Campos calculados
    estoque_atual = serializers.ReadOnlyField()
    estoque_baixo = serializers.ReadOnlyField()
    valor_estoque = serializers.ReadOnlyField()
    margem_lucro_calculada = serializers.ReadOnlyField()
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome_comercial', 'nome_generico', 'codigo_barras',
            'codigo_interno', 'registro_ms', 'categoria', 'categoria_nome',
            'fabricante', 'fabricante_nome', 'tipo_produto', 'apresentacao',
            'concentracao', 'unidade_medida', 'conteudo_embalagem',
            'generico',
            'similar', 'referencia', 'preco_custo', 'preco_venda',
            'margem_lucro', 'estoque_minimo', 'estoque_maximo',
            'ponto_reposicao', 'ativo', 'em_falta', 'descontinuado',
            'descricao', 'indicacoes', 'modo_uso', 'conservacao',
            'observacoes', 'imagem', 'composicao', 'lotes',
            'estoque_atual', 'estoque_baixo', 'valor_estoque',
            'margem_lucro_calculada'
        ]
        read_only_fields = [
            'margem_lucro', 'estoque_atual', 'estoque_baixo', 
            'valor_estoque', 'margem_lucro_calculada'
        ]

class ProdutoResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagens"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    fabricante_nome = serializers.CharField(source='fabricante.nome', read_only=True)
    estoque_atual = serializers.ReadOnlyField()
    estoque_baixo = serializers.ReadOnlyField()
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome_comercial', 'codigo_barras', 'categoria_nome',
            'fabricante_nome', 'apresentacao', 'preco_venda', 'estoque_atual',
            'estoque_baixo', 'ativo'
        ]

