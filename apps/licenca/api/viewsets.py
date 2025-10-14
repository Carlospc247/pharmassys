# apps/licencas/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
from ..models import Licenca, RenovacaoLicenca, DocumentoLicenca, OrgaoRegulador
from .serializers import LicencaSerializer, RenovacaoLicencaSerializer, DocumentoLicencaSerializer, OrgaoReguladorSerializer

class LicencaViewSet(viewsets.ModelViewSet):
    queryset = Licenca.objects.all()
    serializer_class = LicencaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'tipo_licenca', 'orgao_regulador']
    
    @action(detail=False, methods=['get'])
    def vencimentos_proximos(self, request):
        dias = int(request.query_params.get('dias', 30))
        data_limite = date.today() + timedelta(days=dias)
        
        licencas = self.queryset.filter(
            data_vencimento__lte=data_limite,
            data_vencimento__gte=date.today(),
            status='ativa'
        )
        
        serializer = self.get_serializer(licencas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        licenca = self.get_object()
        # Lógica de renovação
        return Response({'status': 'renovação iniciada'})

class RenovacaoLicencaViewSet(viewsets.ModelViewSet):
    queryset = RenovacaoLicenca.objects.all()
    serializer_class = RenovacaoLicencaSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentoLicencaViewSet(viewsets.ModelViewSet):
    queryset = DocumentoLicenca.objects.all()
    serializer_class = DocumentoLicencaSerializer
    permission_classes = [permissions.IsAuthenticated]