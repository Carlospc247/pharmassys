# apps/relatorios/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Relatorio, TemplateRelatorio, AgendamentoRelatorio
from .serializers import RelatorioSerializer, TemplateRelatorioSerializer, AgendamentoRelatorioSerializer

class RelatorioViewSet(viewsets.ModelViewSet):
    queryset = Relatorio.objects.all()
    serializer_class = RelatorioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template', 'status']
    
    @action(detail=True, methods=['post'])
    def gerar(self, request, pk=None):
        relatorio = self.get_object()
        # Lógica de geração do relatório
        return Response({'status': 'relatório gerado'})

class TemplateRelatorioViewSet(viewsets.ModelViewSet):
    queryset = TemplateRelatorio.objects.all()
    serializer_class = TemplateRelatorioSerializer
    permission_classes = [permissions.IsAuthenticated]

class AgendamentoRelatorioViewSet(viewsets.ModelViewSet):
    queryset = AgendamentoRelatorio.objects.all()
    serializer_class = AgendamentoRelatorioSerializer
    permission_classes = [permissions.IsAuthenticated]