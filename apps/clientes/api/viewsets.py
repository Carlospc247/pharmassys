# apps/clientes/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Cliente, EnderecoCliente, TelefoneCliente, GrupoCliente, ProgramaFidelidade
from .serializers import ClienteSerializer, EnderecoClienteSerializer, TelefoneClienteSerializer, GrupoClienteSerializer, ProgramaFidelidadeSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ativo', 'grupo', 'data_nascimento']
    
    @action(detail=True, methods=['get'])
    def historico_compras(self, request, pk=None):
        cliente = self.get_object()
        # Retornar histórico de compras
        return Response({'historico': 'implementar'})
    
    @action(detail=True, methods=['get'])
    def pontos_fidelidade(self, request, pk=None):
        cliente = self.get_object()
        try:
            programa = cliente.programa_fidelidade
            serializer = ProgramaFidelidadeSerializer(programa)
            return Response(serializer.data)
        except ProgramaFidelidade.DoesNotExist:
            return Response({'pontos': 0})

class EnderecoClienteViewSet(viewsets.ModelViewSet):
    queryset = EnderecoCliente.objects.all()
    serializer_class = EnderecoClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class TelefoneClienteViewSet(viewsets.ModelViewSet):
    queryset = TelefoneCliente.objects.all()
    serializer_class = TelefoneClienteSerializer
    permission_classes = [permissions.IsAuthenticated]