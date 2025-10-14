# apps/configuracoes/api/serializers.py
from rest_framework import serializers
from ..models import  PersonalizacaoInterface, BackupConfiguracao

class ParametroSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalizacaoInterface
        fields = '__all__'


class BackupSerializer(serializers.ModelSerializer):
    tamanho_formatado = serializers.CharField(read_only=True)
    
    class Meta:
        model = BackupConfiguracao
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']