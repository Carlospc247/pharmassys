# apps/funcionarios/api/viewsets.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Funcionario, Cargo, Departamento, RegistroPonto, Ferias
from .serializers import FuncionarioSerializer, CargoSerializer, DepartamentoSerializer, PontoEletronicoSerializer, FeriasSerializer  # ajustar o serializer também

class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ativo', 'cargo', 'departamento']
    
    @action(detail=True, methods=['get'])
    def ponto_mes(self, request, pk=None):
        funcionario = self.get_object()
        mes = request.query_params.get('mes', '').split('-')
        if len(mes) == 2:
            pontos = RegistroPonto.objects.filter(
                funcionario=funcionario,
                data_registro__year=int(mes[0]),
                data_registro__month=int(mes[1])
            )
            serializer = RegistroPontoSerializer(pontos, many=True)
            return Response(serializer.data)
        return Response({'error': 'Formato de mês inválido (YYYY-MM)'})

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
