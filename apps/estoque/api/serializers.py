# apps/estoque/api/serializers.py
from rest_framework import serializers
from ..models import LocalizacaoEstoque, MovimentacaoEstoque, Inventario, ItemInventario

class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacaoEstoque
        fields = '__all__'

class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = MovimentacaoEstoque
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ItemInventarioSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    diferenca = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    
    class Meta:
        model = ItemInventario
        fields = '__all__'

class InventarioSerializer(serializers.ModelSerializer):
    itens = ItemInventarioSerializer(many=True, read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    
    class Meta:
        model = Inventario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class TransferenciaEstoqueSerializer(serializers.ModelSerializer):
    loja_origem_nome = serializers.CharField(source='loja_origem.nome', read_only=True)
    loja_destino_nome = serializers.CharField(source='loja_destino.nome', read_only=True)
    
    class Meta:
        model = MovimentacaoEstoque
        fields = '__all__'
        read_only_fields = ['numero_transferencia', 'created_at', 'updated_at']