# apps/comanda/api/serializers.py
from rest_framework import serializers
from decimal import Decimal
from ..models import (
    Mesa, Comanda, ItemComanda, StatusComanda,
    HistoricoComanda, ConfiguracaoComanda
)

class ConfiguracaoComandaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    
    class Meta:
        model = ConfiguracaoComanda
        fields = [
            'id', 'loja', 'loja_nome', 'tempo_limite_mesa',
            'permite_desconto', 'desconto_maximo_percentual',
            'percentual_gorjeta_padrao', 'permite_divisao_conta',
            'ativa', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class MesaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    localizacao_display = serializers.CharField(source='get_localizacao_display', read_only=True)
    comanda_ativa = serializers.SerializerMethodField()
    tempo_ocupacao = serializers.SerializerMethodField()
    
    class Meta:
        model = Mesa
        fields = [
            'id', 'numero', 'capacidade', 'descricao', 'loja',
            'loja_nome', 'localizacao', 'localizacao_display',
            'coordenada_x', 'coordenada_y', 'status', 'status_display',
            'ativa', 'observacoes', 'comanda_ativa', 'tempo_ocupacao',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_comanda_ativa(self, obj):
        comanda = obj.comandas.filter(status__in=['aberta', 'em_andamento']).first()
        if comanda:
            return {
                'id': comanda.id,
                'numero_comanda': comanda.numero_comanda,
                'total': comanda.total,
                'total_itens': comanda.itens.count(),
                'cliente': comanda.cliente.nome if comanda.cliente else None
            }
        return None
    
    def get_tempo_ocupacao(self, obj):
        from django.utils import timezone
        comanda = obj.comandas.filter(status__in=['aberta', 'em_andamento']).first()
        if comanda and comanda.data_abertura:
            delta = timezone.now() - comanda.data_abertura
            horas = int(delta.total_seconds() / 3600)
            minutos = int((delta.total_seconds() % 3600) / 60)
            return f"{horas}h {minutos}m"
        return None

class StatusComandaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    status_anterior_display = serializers.CharField(source='get_status_anterior_display', read_only=True)
    status_novo_display = serializers.CharField(source='get_status_novo_display', read_only=True)
    
    class Meta:
        model = StatusComanda
        fields = [
            'id', 'comanda', 'status_anterior', 'status_anterior_display',
            'status_novo', 'status_novo_display', 'data_mudanca',
            'usuario', 'usuario_nome', 'observacoes'
        ]

class HistoricoComandaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)
    
    class Meta:
        model = HistoricoComanda
        fields = [
            'id', 'comanda', 'acao', 'acao_display', 'descricao',
            'dados_anteriores', 'dados_novos', 'data_acao',
            'usuario', 'usuario_nome'
        ]

class ItemComandaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_barras', read_only=True)
    categoria_nome = serializers.CharField(source='produto.categoria.nome', read_only=True)
    status_item_display = serializers.CharField(source='get_status_item_display', read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    valor_desconto_item = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    valor_final_item = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemComanda
        fields = [
            'id', 'comanda', 'produto', 'produto_nome', 'produto_codigo',
            'categoria_nome', 'quantidade', 'preco_unitario', 'desconto',
            'total', 'valor_desconto_item', 'valor_final_item',
            'status_item', 'status_item_display', 'data_pedido',
            'data_preparo', 'data_entrega', 'observacoes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['data_pedido', 'total', 'created_at', 'updated_at']
    
    def get_valor_final_item(self, obj):
        return obj.total - obj.desconto
    
    def validate_quantidade(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero")
        return value
    
    def validate_desconto(self, value):
        if value < 0:
            raise serializers.ValidationError("Desconto não pode ser negativo")
        return value
    
    def validate(self, data):
        # Validar se desconto não é maior que valor total
        quantidade = data.get('quantidade', 0)
        preco_unitario = data.get('preco_unitario', 0)
        desconto = data.get('desconto', 0)
        
        total = quantidade * preco_unitario
        
        if desconto > total:
            raise serializers.ValidationError(
                "Desconto não pode ser maior que o valor total do item"
            )
        
        return data

class ComandaSerializer(serializers.ModelSerializer):
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    mesa_localizacao = serializers.CharField(source='mesa.get_localizacao_display', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Itens da comanda
    itens = ItemComandaSerializer(many=True, read_only=True)
    itens_ativos = serializers.SerializerMethodField()
    
    # Histórico e mudanças de status
    historico = HistoricoComandaSerializer(many=True, read_only=True)
    mudancas_status = StatusComandaSerializer(many=True, read_only=True)
    
    # Campos calculados
    total_itens = serializers.SerializerMethodField()
    tempo_mesa = serializers.SerializerMethodField()
    pode_adicionar_itens = serializers.SerializerMethodField()
    pode_fechar = serializers.SerializerMethodField()
    percentual_gorjeta = serializers.SerializerMethodField()
    valor_com_gorjeta = serializers.SerializerMethodField()
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'mesa', 'mesa_numero', 'mesa_localizacao',
            'cliente', 'cliente_nome', 'funcionario', 'funcionario_nome',
            'loja', 'loja_nome', 'data_abertura', 'data_fechamento',
            'valor_subtotal', 'valor_desconto', 'valor_acrescimo',
            'total', 'gorjeta', 'percentual_gorjeta', 'valor_com_gorjeta',
            'status', 'status_display', 'observacoes', 'itens', 'itens_ativos',
            'total_itens', 'tempo_mesa', 'pode_adicionar_itens', 'pode_fechar',
            'historico', 'mudancas_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'numero_comanda', 'valor_subtotal', 'total',
            'data_abertura', 'created_at', 'updated_at'
        ]
    
    def get_itens_ativos(self, obj):
        itens_ativos = obj.itens.exclude(status_item='cancelado')
        return ItemComandaSerializer(itens_ativos, many=True).data
    
    def get_total_itens(self, obj):
        return obj.itens.exclude(status_item='cancelado').count()
    
    def get_tempo_mesa(self, obj):
        if obj.data_abertura:
            from django.utils import timezone
            if obj.data_fechamento:
                delta = obj.data_fechamento - obj.data_abertura
            else:
                delta = timezone.now() - obj.data_abertura
            
            total_minutos = int(delta.total_seconds() / 60)
            horas = total_minutos // 60
            minutos = total_minutos % 60
            
            if horas > 0:
                return f"{horas}h {minutos}m"
            else:
                return f"{minutos}m"
        return "0m"
    
    def get_pode_adicionar_itens(self, obj):
        return obj.status in ['aberta', 'em_andamento']
    
    def get_pode_fechar(self, obj):
        return (
            obj.status in ['aberta', 'em_andamento'] and
            obj.itens.exclude(status_item='cancelado').exists()
        )
    
    def get_percentual_gorjeta(self, obj):
        if obj.valor_subtotal and obj.valor_subtotal > 0 and obj.gorjeta:
            return round((obj.gorjeta / obj.valor_subtotal) * 100, 2)
        return 0
    
    def get_valor_com_gorjeta(self, obj):
        return obj.total + (obj.gorjeta or 0)
    
    def validate_valor_desconto(self, value):
        if value < 0:
            raise serializers.ValidationError("Desconto não pode ser negativo")
        return value
    
    def validate_valor_acrescimo(self, value):
        if value < 0:
            raise serializers.ValidationError("Acréscimo não pode ser negativo")
        return value
    
    def validate_gorjeta(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Gorjeta não pode ser negativa")
        return value

# Serializers para operações específicas
class AdicionarItemComandaSerializer(serializers.Serializer):
    """Serializer para adicionar item à comanda"""
    produto_id = serializers.IntegerField()
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=3, min_value=0.001)
    preco_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    desconto = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, min_value=0)
    observacoes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_produto_id(self, value):
        from apps.produtos.models import Produto
        try:
            produto = Produto.objects.get(id=value, ativo=True)
            return value
        except Produto.DoesNotExist:
            raise serializers.ValidationError("Produto não encontrado ou inativo")

class AplicarDescontoComandaSerializer(serializers.Serializer):
    """Serializer para aplicar desconto à comanda"""
    TIPO_CHOICES = [('valor', 'Valor'), ('percentual', 'Percentual')]
    
    tipo_desconto = serializers.ChoiceField(choices=TIPO_CHOICES, default='valor')
    valor_desconto = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    motivo_desconto = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    def validate(self, data):
        if data['tipo_desconto'] == 'percentual' and data['valor_desconto'] > 100:
            raise serializers.ValidationError(
                "Percentual de desconto não pode ser maior que 100%"
            )
        return data

class FecharComandaSerializer(serializers.Serializer):
    """Serializer para fechar comanda"""
    gorjeta = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, min_value=0)
    observacoes_fechamento = serializers.CharField(max_length=500, required=False, allow_blank=True)
    forma_pagamento = serializers.CharField(max_length=50, required=False)

class TransferirMesaSerializer(serializers.Serializer):
    """Serializer para transferir comanda para outra mesa"""
    nova_mesa_id = serializers.IntegerField()
    motivo_transferencia = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    def validate_nova_mesa_id(self, value):
        try:
            mesa = Mesa.objects.get(id=value, ativa=True)
            if mesa.status != 'disponivel':
                raise serializers.ValidationError("Mesa de destino não está disponível")
            return value
        except Mesa.DoesNotExist:
            raise serializers.ValidationError("Mesa não encontrada ou inativa")

# Serializers resumidos para listas
class ComandaResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para listas"""
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_itens = serializers.SerializerMethodField()
    tempo_mesa = serializers.SerializerMethodField()
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'mesa_numero', 'cliente_nome',
            'data_abertura', 'total', 'status', 'status_display',
            'total_itens', 'tempo_mesa'
        ]
    
    def get_total_itens(self, obj):
        return obj.itens.exclude(status_item='cancelado').count()
    
    def get_tempo_mesa(self, obj):
        if obj.data_abertura:
            from django.utils import timezone
            if obj.data_fechamento:
                delta = obj.data_fechamento - obj.data_abertura
            else:
                delta = timezone.now() - obj.data_abertura
            
            total_minutos = int(delta.total_seconds() / 60)
            horas = total_minutos // 60
            minutos = total_minutos % 60
            
            if horas > 0:
                return f"{horas}h {minutos}m"
            else:
                return f"{minutos}m"
        return "0m"

class MesaResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para mapa de mesas"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Mesa
        fields = [
            'id', 'numero', 'capacidade', 'localizacao',
            'coordenada_x', 'coordenada_y', 'status', 'status_display'
        ]