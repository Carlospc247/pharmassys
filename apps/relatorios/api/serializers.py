# apps/relatorios/api/serializers.py
from rest_framework import serializers
from ..models import Relatorio, TemplateRelatorio, AgendamentoRelatorio

class TemplateRelatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateRelatorio
        fields = '__all__'

class AgendamentoRelatorioSerializer(serializers.ModelSerializer):
    relatorio_nome = serializers.CharField(source='relatorio.nome', read_only=True)
    
    class Meta:
        model = AgendamentoRelatorio
        fields = '__all__'

class RelatorioSerializer(serializers.ModelSerializer):
    template_nome = serializers.CharField(source='template.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Relatorio
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']