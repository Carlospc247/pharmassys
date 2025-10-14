# apps/core/api/viewsets.py
"""from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django# apps/core/api/viewsets.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from datetime import date, timedelta
from ..models import Empresa, Loja
from .serializers import EmpresaSerializer, LojaSerializer, UsuarioSerializer
"""
# apps/core/api/viewsets.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from datetime import date, timedelta

from ..models import Empresa, Loja
from .serializers import EmpresaSerializer, LojaSerializer, UsuarioSerializer
from django_filters.rest_framework import DjangoFilterBackend



User = get_user_model()

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'nif', 'razao_social']
    filterset_fields = ['ativa', 'tipo_empresa']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']
    
    def get_queryset(self):
        # Se não for superuser, mostrar apenas sua empresa
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'empresa'):
                return self.queryset.filter(id=self.request.user.empresa.id)
        return self.queryset
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Retorna estatísticas da empresa"""
        empresa = self.get_object()
        
        # Contar lojas
        total_lojas = empresa.lojas.count()
        lojas_ativas = empresa.lojas.filter(ativa=True).count()
        
        # Contar usuários
        total_usuarios = User.objects.filter(empresa=empresa).count()
        usuarios_ativos = User.objects.filter(empresa=empresa, is_active=True).count()
        
        return Response({
            'total_lojas': total_lojas,
            'lojas_ativas': lojas_ativas,
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
        })
    
    @action(detail=True, methods=['post'])
    def ativar_desativar(self, request, pk=None):
        """Ativa ou desativa empresa"""
        empresa = self.get_object()
        empresa.ativa = not empresa.ativa
        empresa.save()
        
        status_text = 'ativada' if empresa.ativa else 'desativada'
        return Response({
            'message': f'Empresa {status_text} com sucesso',
            'ativa': empresa.ativa
        })

class LojaViewSet(viewsets.ModelViewSet):
    queryset = Loja.objects.all()
    serializer_class = LojaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'endereco', 'cidade']
    filterset_fields = ['empresa', 'ativa', 'provincia']
    ordering_fields = ['nome', 'created_at']
    ordering = ['nome']
    
    def get_queryset(self):
        # Filtrar por empresa do usuário
        if hasattr(self.request.user, 'empresa') and not self.request.user.is_superuser:
            return self.queryset.filter(empresa=self.request.user.empresa)
        return self.queryset
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Retorna dados do dashboard da loja"""
        loja = self.get_object()
        
        # Aqui você implementaria as estatísticas específicas da loja
        # Por enquanto, retornando estrutura básica
        return Response({
            'loja': self.get_serializer(loja).data,
            'vendas_hoje': 0,  # Implementar quando tiver model de vendas
            'produtos_estoque_baixo': 0,  # Implementar quando tiver model de estoque
            'clientes_cadastrados': 0,  # Implementar quando tiver model de clientes
        })
    
    @action(detail=True, methods=['post'])
    def ativar_desativar(self, request, pk=None):
        """Ativa ou desativa loja"""
        loja = self.get_object()
        loja.ativa = not loja.ativa
        loja.save()
        
        status_text = 'ativada' if loja.ativa else 'desativada'
        return Response({
            'message': f'Loja {status_text} com sucesso',
            'ativa': loja.ativa
        })

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'sobrenome', 'email']
    filterset_fields = ['empresa', 'is_active', 'is_staff', 'is_superuser']
    ordering_fields = ['nome', 'email', 'date_joined']
    ordering = ['nome']
    
    def get_queryset(self):
        # Filtrar por empresa do usuário se não for superuser
        if hasattr(self.request.user, 'empresa') and not self.request.user.is_superuser:
            return self.queryset.filter(empresa=self.request.user.empresa)
        return self.queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna dados do usuário logado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ativar_desativar(self, request, pk=None):
        """Ativa ou desativa usuário"""
        usuario = self.get_object()
        
        # Não permitir desativar próprio usuário
        if usuario == request.user:
            return Response(
                {'error': 'Não é possível desativar seu próprio usuário'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario.is_active = not usuario.is_active
        usuario.save()
        
        status_text = 'ativado' if usuario.is_active else 'desativado'
        return Response({
            'message': f'Usuário {status_text} com sucesso',
            'is_active': usuario.is_active
        })
    
    @action(detail=True, methods=['post'])
    def resetar_senha(self, request, pk=None):
        """Envia email para reset de senha"""
        usuario = self.get_object()
        
        # Aqui você implementaria o envio do email
        # Por enquanto, apenas simulando
        return Response({
            'message': 'Email de reset de senha enviado com sucesso'
        })
    
    @action(detail=False, methods=['get'])
    def online(self, request):
        """Retorna usuários online (logados nas últimas 15 minutos)"""
        from django.utils import timezone
        
        limite_online = timezone.now() - timedelta(minutes=15)
        usuarios_online = self.get_queryset().filter(
            last_login__gte=limite_online
        )
        
        serializer = self.get_serializer(usuarios_online, many=True)
        return Response(serializer.data)
from ..models import *
from .serializers import *

# Adicionar viewsets específicos da app aqui
