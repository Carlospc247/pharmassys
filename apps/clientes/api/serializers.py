# apps/clientes/api/serializers.py
from rest_framework import serializers
from ..models import Cliente, EnderecoCliente, TelefoneCliente, GrupoCliente, ProgramaFidelidade

class EnderecoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnderecoCliente
        fields = '__all__'

class TelefoneClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelefoneCliente
        fields = '__all__'

class GrupoClienteSerializer(serializers.ModelSerializer):
    total_clientes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = GrupoCliente
        fields = '__all__'

class ProgramaFidelidadeSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    
    class Meta:
        model = ProgramaFidelidade
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    enderecos = EnderecoClienteSerializer(many=True, read_only=True)
    telefones = TelefoneClienteSerializer(many=True, read_only=True)
    idade = serializers.IntegerField(read_only=True)
    total_compras = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']