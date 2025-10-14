# apps/core/api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Empresa, Loja

User = get_user_model()

class EmpresaSerializer(serializers.ModelSerializer):
    total_lojas = serializers.SerializerMethodField()
    total_usuarios = serializers.SerializerMethodField()
    
    class Meta:
        model = Empresa
        fields = [
            'id', 'nome', 'razao_social', 'nif',
            'endereco', 'cidade', 'provincia', 'postal', 'telefone', 'email',
            'website', 'logo', 'ativa', 'tipo_empresa', 'total_lojas',
            'total_usuarios', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_lojas(self, obj):
        return obj.lojas.count()
    
    def get_total_usuarios(self, obj):
        return User.objects.filter(empresa=obj).count()

class LojaSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    
    class Meta:
        model = Loja
        fields = [
            'id', 'nome', 'empresa', 'empresa_nome', 'endereco',
            'cidade', 'provincia', 'postal', 'telefone', 'email',
            'nif', 'responsavel',
            'ativa', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class UsuarioSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    nome_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nome', 'sobrenome', 'nome_completo',
            'telefone', 'empresa', 'empresa_nome', 'is_active',
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_nome_completo(self, obj):
        return f"{obj.nome} {obj.sobrenome}".strip()
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user