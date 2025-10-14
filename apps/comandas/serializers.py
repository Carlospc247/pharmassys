# apps/comandas/serializers.py
from rest_framework import serializers
from .models import (
    CentroRequisicao, Comanda, ItemComanda, 
    MovimentacaoComanda, TemplateComanda, ItemTemplateComanda
)

class CentroRequisicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroRequisicao
        fields = ['id', 'nome', 'tipo', 'responsavel', 'documento_responsavel', 
                 'telefone', 'email', 'endereco', 'ativo']

class ItemComandaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_barras', read_only=True)
    categoria_nome = serializers.CharField(source='produto.categoria.nome', read_only=True)
    percentual_atendido = serializers.ReadOnlyField()
    saldo_pendente = serializers.ReadOnlyField()
    atendido_por_nome = serializers.CharField(source='atendido_por.get_full_name', read_only=True)
    
    class Meta:
        model = ItemComanda
        fields = [
            'id', 'produto', 'produto_nome', 'produto_codigo', 'categoria_nome',
            'lote', 'quantidade_solicitada', 'quantidade_atendida', 'quantidade_cancelada',
            'unidade_medida', 'preco_unitario', 'subtotal', 'justificativa_item',
            'observacoes_item', 'status', 'percentual_atendido', 'saldo_pendente',
            'data_atendimento', 'atendido_por', 'atendido_por_nome'
        ]
        read_only_fields = ['subtotal', 'percentual_atendido', 'saldo_pendente']

class MovimentacaoComandaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = MovimentacaoComanda
        fields = ['id', 'acao', 'descricao', 'observacoes', 'usuario_nome', 'created_at']

class ComandaSerializer(serializers.ModelSerializer):
    centro_requisicao_nome = serializers.CharField(source='centro_requisicao.nome', read_only=True)
    solicitante_nome = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    atendente_nome = serializers.CharField(source='atendente.get_full_name', read_only=True)
    aprovador_nome = serializers.CharField(source='aprovador.get_full_name', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    
    itens = ItemComandaSerializer(many=True, read_only=True)
    movimentacoes = MovimentacaoComandaSerializer(many=True, read_only=True)
    
    percentual_atendido = serializers.ReadOnlyField()
    total_itens = serializers.ReadOnlyField()
    tempo_atendimento = serializers.ReadOnlyField()
    
    # Campos calculados
    dias_em_aberto = serializers.SerializerMethodField()
    status_prazo = serializers.SerializerMethodField()
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'centro_requisicao', 'centro_requisicao_nome',
            'tipo_comanda', 'status', 'prioridade', 'solicitante', 'solicitante_nome',
            'atendente', 'atendente_nome', 'aprovador', 'aprovador_nome',
            'data_solicitacao', 'data_inicio_atendimento', 'data_finalizacao', 'data_prazo',
            'descricao', 'justificativa', 'observacoes', 'observacoes_atendimento',
            'valor_estimado', 'valor_real', 'loja', 'loja_nome', 'requer_aprovacao',
            'aprovada', 'data_aprovacao', 'itens', 'movimentacoes',
            'percentual_atendido', 'total_itens', 'tempo_atendimento',
            'dias_em_aberto', 'status_prazo', 'created_at'
        ]
        read_only_fields = [
            'numero_comanda', 'valor_estimado', 'valor_real', 'percentual_atendido',
            'total_itens', 'tempo_atendimento', 'requer_aprovacao'
        ]
    
    def get_dias_em_aberto(self, obj):
        """Calcula há quantos dias a comanda está em aberto"""
        if obj.status in ['finalizada', 'cancelada']:
            return 0
        
        from datetime import datetime
        from django.utils import timezone
        
        now = timezone.now()
        delta = now - obj.data_solicitacao
        return delta.days
    
    def get_status_prazo(self, obj):
        """Retorna status em relação ao prazo"""
        if not obj.data_prazo or obj.status in ['finalizada', 'cancelada']:
            return 'sem_prazo'
        
        from django.utils import timezone
        now = timezone.now()
        
        if now > obj.data_prazo:
            return 'atrasada'
        elif (obj.data_prazo - now).days <= 1:
            return 'vencendo'
        else:
            return 'no_prazo'

class ItemTemplateComandaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    
    class Meta:
        model = ItemTemplateComanda
        fields = ['id', 'produto', 'produto_nome', 'quantidade_padrao', 
                 'unidade_medida', 'justificativa_padrao', 'ordem']

class TemplateComandaSerializer(serializers.ModelSerializer):
    centro_requisicao_nome = serializers.CharField(source='centro_requisicao.nome', read_only=True)
    itens_template = ItemTemplateComandaSerializer(many=True, read_only=True)
    total_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateComanda
        fields = ['id', 'nome', 'tipo_comanda', 'centro_requisicao', 
                 'centro_requisicao_nome', 'descricao', 'ativo', 
                 'itens_template', 'total_itens', 'created_at']
    
    def get_total_itens(self, obj):
        return obj.itens_template.count()

class ComandaResumoSerializer(serializers.ModelSerializer):
    """Serializer para listagem resumida de comandas"""
    solicitante_nome = serializers.CharField(source='solicitante.get_full_name', read_only=True)
    tipo_comanda_display = serializers.CharField(source='get_tipo_comanda_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    percentual_atendido = serializers.ReadOnlyField()
    total_itens = serializers.ReadOnlyField()
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'tipo_comanda', 'tipo_comanda_display',
            'status', 'status_display', 'prioridade', 'prioridade_display',
            'solicitante_nome', 'data_solicitacao', 'valor_estimado',
            'percentual_atendido', 'total_itens'
        ]