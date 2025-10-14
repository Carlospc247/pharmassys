# apps/funcionarios/api/serializers.py
from rest_framework import serializers
from ..models import Funcionario, Cargo, Departamento, RegistroPonto, Ferias


class CargoSerializer(serializers.ModelSerializer):
    total_funcionarios = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cargo
        fields = '__all__'

class DepartamentoSerializer(serializers.ModelSerializer):
    total_funcionarios = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Departamento
        fields = '__all__'

class PontoEletronicoSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    
    class Meta:
        model = RegistroPonto
        fields = '__all__'

class FeriasSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    total_dias = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Ferias
        fields = '__all__'

class FuncionarioSerializer(serializers.ModelSerializer):
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    idade = serializers.IntegerField(read_only=True)
    tempo_empresa = serializers.CharField(read_only=True)
    
    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']