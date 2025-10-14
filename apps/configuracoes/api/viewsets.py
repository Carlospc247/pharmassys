# apps/configuracoes/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.configuracoes.models import BackupConfiguracao, PersonalizacaoInterface

from .serializers import  ParametroSistemaSerializer, BackupSerializer



class ParametroSistemaViewSet(viewsets.ModelViewSet):
    queryset = PersonalizacaoInterface.objects.all()
    serializer_class = ParametroSistemaSerializer
    permission_classes = [permissions.IsAuthenticated]

class BackupViewSet(viewsets.ModelViewSet):
    queryset = BackupConfiguracao.objects.all()
    serializer_class = BackupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def criar_backup(self, request):
        # Lógica de criação de backup
        return Response({'status': 'backup iniciado'})

