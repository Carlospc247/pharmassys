# apps/fornecedores/api/serializers.py
from rest_framework import serializers
from ..models import DocumentoFornecedor, Fornecedor, ContatoFornecedor, Pedido, ItemPedido, AvaliacaoFornecedor
from apps.produtos.models import Produto




class ContatoFornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContatoFornecedor
        fields = '__all__'

class FornecedorSerializer(serializers.ModelSerializer):
    contatos = ContatoFornecedorSerializer(many=True, read_only=True)
    total_pedidos = serializers.IntegerField(read_only=True)
    total_compras = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Fornecedor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ItemPedidoCompraSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    
    class Meta:
        model = ItemPedido
        fields = '__all__'

class PedidoCompraSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    itens = ItemPedidoCompraSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ['numero_pedido', 'created_at', 'updated_at']

class AvaliacaoFornecedorSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    
    class Meta:
        model = AvaliacaoFornecedor
        fields = '__all__'

class ContatoFornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContatoFornecedor
        fields = ['id', 'nome', 'cargo', 'tipo_contato', 'telefone', 'celular', 'email', 'principal', 'ativo']

class DocumentoFornecedorSerializer(serializers.ModelSerializer):
    vencido = serializers.ReadOnlyField()
    usuario_upload_nome = serializers.CharField(source='usuario_upload.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentoFornecedor
        fields = ['id', 'tipo_documento', 'nome_documento', 'arquivo', 'data_validade', 
                 'observacoes', 'vencido', 'usuario_upload_nome', 'created_at']


class AvaliacaoFornecedorSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero_pedido', read_only=True)
    
    class Meta:
        model = AvaliacaoFornecedor
        fields = ['id', 'criterio', 'nota', 'comentarios', 'usuario_nome', 'pedido_numero', 'created_at']


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    estoque_atual = serializers.IntegerField(source='get_estoque_disponivel', read_only=True)
    preco_formatado = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            'id',
            'nome',
            'codigo',
            'categoria',
            'categoria_nome',
            'descricao',
            'preco',
            'preco_formatado',
            'estoque_atual',
            'ativo',
            'created_at',
            'updated_at'
        ]

    def get_preco_formatado(self, obj):
        return f"R$ {obj.preco:.2f}" if obj.preco else "R$ 0.00"

