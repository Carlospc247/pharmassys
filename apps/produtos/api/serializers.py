# apps/produtos/api/serializers.py
from rest_framework import serializers
from ..models import Categoria, Fabricante, Produto, Lote, Preco

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class FabricanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fabricante
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    fabricante_nome = serializers.CharField(source='fabricante.nome', read_only=True)
    preco_atual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    estoque_atual = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'codigo_interno']

class LoteSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Lote
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PrecoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    
    class Meta:
        model = Preco
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']