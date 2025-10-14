# apps/licencas/api/serializers.py
from rest_framework import serializers
from ..models import Licenca, RenovacaoLicenca, DocumentoLicenca, OrgaoRegulador

class OrgaoReguladorSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgaoRegulador
        fields = '__all__'

class DocumentoLicencaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoLicenca
        fields = '__all__'

class RenovacaoLicencaSerializer(serializers.ModelSerializer):
    licenca_numero = serializers.CharField(source='licenca.numero_licenca', read_only=True)
    
    class Meta:
        model = RenovacaoLicenca
        fields = '__all__'

class LicencaSerializer(serializers.ModelSerializer):
    orgao_nome = serializers.CharField(source='orgao_regulador.nome', read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)
    documentos = DocumentoLicencaSerializer(many=True, read_only=True)
    renovacoes = RenovacaoLicencaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Licenca
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']