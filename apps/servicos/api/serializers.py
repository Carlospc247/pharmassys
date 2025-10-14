# apps/servicos/api/serializers.py
from rest_framework import serializers
from ..models import (
     Servico, AplicacaoVacina, TesteRapido,
    AfericaoParametros, ConsultoriaFarmaceutica, AgendamentoServico
)

class AgendamentoServicoSerializer(serializers.ModelSerializer):
    farmaceutico_nome = serializers.CharField(source='farmaceutico.nome', read_only=True)
    servico_tipo = serializers.CharField(source='servico.servico.nome', read_only=True)
    paciente_nome = serializers.CharField(source='servico.paciente.cliente.nome_completo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AgendamentoServico
        fields = [
            'id', 'farmaceutico', 'farmaceutico_nome', 'data_hora',
            'duracao_minutos', 'status', 'status_display', 'servico',
            'servico_tipo', 'paciente_nome', 'observacoes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class AplicacaoVacinaSerializer(serializers.ModelSerializer):
    vacina_nome = serializers.CharField(source='vacina.nome_comercial', read_only=True)
    paciente_nome = serializers.CharField(source='servico.paciente.cliente.nome_completo', read_only=True)
    farmaceutico_nome = serializers.CharField(source='servico.farmaceutico.nome', read_only=True)
    local_aplicacao_display = serializers.CharField(source='get_local_aplicacao_display', read_only=True)
    via_administracao_display = serializers.CharField(source='get_via_administracao_display', read_only=True)
    gravidade_reacao_display = serializers.CharField(source='get_gravidade_reacao_display', read_only=True)
    
    class Meta:
        model = AplicacaoVacina
        fields = [
            'id', 'servico', 'vacina', 'vacina_nome', 'paciente_nome',
            'farmaceutico_nome', 'lote_vacina', 'validade_vacina',
            'fabricante_vacina', 'local_aplicacao', 'local_aplicacao_display',
            'via_administracao', 'via_administracao_display', 'dose_ml',
            'teve_reacao', 'tipo_reacao', 'gravidade_reacao',
            'gravidade_reacao_display', 'proxima_dose_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TesteRapidoSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source='servico.paciente.cliente.nome_completo', read_only=True)
    farmaceutico_nome = serializers.CharField(source='servico.farmaceutico.nome', read_only=True)
    tipo_teste_display = serializers.CharField(source='get_tipo_teste_display', read_only=True)
    tipo_amostra_display = serializers.CharField(source='get_tipo_amostra_display', read_only=True)
    resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
    controle_qualidade_ok = serializers.SerializerMethodField()
    
    class Meta:
        model = TesteRapido
        fields = [
            'id', 'servico', 'paciente_nome', 'farmaceutico_nome',
            'tipo_teste', 'tipo_teste_display', 'nome_teste',
            'fabricante_teste', 'lote_teste', 'validade_teste',
            'tipo_amostra', 'tipo_amostra_display', 'resultado',
            'resultado_display', 'valor_numerico', 'unidade_medida',
            'valores_referencia', 'observacoes_coleta',
            'observacoes_resultado', 'controle_positivo',
            'controle_negativo', 'controle_qualidade_ok',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_controle_qualidade_ok(self, obj):
        return obj.controle_positivo and obj.controle_negativo

class AfericaoParametrosSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source='servico.paciente.cliente.nome_completo', read_only=True)
    farmaceutico_nome = serializers.CharField(source='servico.farmaceutico.nome', read_only=True)
    pressao_arterial = serializers.SerializerMethodField()
    imc_atual = serializers.DecimalField(source='imc', max_digits=5, decimal_places=2, read_only=True)
    classificacao_pressao_arterial = serializers.CharField(source='classificacao_pressao', read_only=True)
    
    class Meta:
        model = AfericaoParametros
        fields = [
            'id', 'servico', 'paciente_nome', 'farmaceutico_nome',
            'pressao_sistolica', 'pressao_diastolica', 'pressao_arterial',
            'classificacao_pressao_arterial', 'frequencia_cardiaca',
            'temperatura', 'saturacao_oxigenio', 'peso', 'altura',
            'imc_atual', 'glicemia_jejum', 'glicemia_pos_prandial',
            'condicoes_afericao', 'equipamentos_utilizados',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_pressao_arterial(self, obj):
        if obj.pressao_sistolica and obj.pressao_diastolica:
            return f"{obj.pressao_sistolica}/{obj.pressao_diastolica} mmHg"
        return None

class ConsultoriaFarmaceuticaSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source='servico.paciente.cliente.nome_completo', read_only=True)
    farmaceutico_nome = serializers.CharField(source='servico.farmaceutico.nome', read_only=True)
    tipo_consultoria_display = serializers.CharField(source='get_tipo_consultoria_display', read_only=True)
    
    class Meta:
        model = ConsultoriaFarmaceutica
        fields = [
            'id', 'servico', 'paciente_nome', 'farmaceutico_nome',
            'tipo_consultoria', 'tipo_consultoria_display',
            'medicamentos_envolvidos', 'problema_identificado',
            'analise_farmaceutica', 'referencias_consultadas',
            'recomendacoes_farmaceuticas', 'alternativas_terapeuticas',
            'necessita_seguimento', 'data_seguimento',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ServicoSerializer(serializers.ModelSerializer):
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    servico_categoria = serializers.CharField(source='servico.categoria', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.cliente.nome_completo', read_only=True)
    paciente_prontuario = serializers.CharField(source='paciente.numero_prontuario', read_only=True)
    farmaceutico_nome = serializers.CharField(source='farmaceutico.nome', read_only=True)
    usuario_criacao_nome = serializers.CharField(source='usuario_criacao.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Dados específicos do tipo de serviço
    aplicacao_vacina = AplicacaoVacinaSerializer(read_only=True)
    teste_rapido = TesteRapidoSerializer(read_only=True)
    afericao_parametros = AfericaoParametrosSerializer(read_only=True)
    consultoria_farmaceutica = ConsultoriaFarmaceuticaSerializer(read_only=True)
    agendamento = AgendamentoServicoSerializer(read_only=True)
    
    # Campos calculados
    duracao_real = serializers.SerializerMethodField()
    tempo_desde_agendamento = serializers.SerializerMethodField()
    pode_ser_iniciado = serializers.SerializerMethodField()
    pode_ser_finalizado = serializers.SerializerMethodField()
    
    class Meta:
        model = Servico
        fields = [
            'id', 'numero_servico', 'servico', 'servico_nome',
            'servico_categoria', 'paciente', 'paciente_nome',
            'paciente_prontuario', 'farmaceutico', 'farmaceutico_nome',
            'data_agendamento', 'data_realizacao', 'duracao_minutos',
            'duracao_real', 'tempo_desde_agendamento', 'preco_servico',
            'desconto', 'valor_final', 'status', 'status_display',
            'observacoes_agendamento', 'observacoes_realizacao',
            'resultado_servico', 'recomendacoes', 'avaliacao_cliente',
            'comentario_cliente', 'usuario_criacao', 'usuario_criacao_nome',
            'pode_ser_iniciado', 'pode_ser_finalizado',
            'aplicacao_vacina', 'teste_rapido', 'afericao_parametros',
            'consultoria_farmaceutica', 'agendamento',
            'data_criacao', 'updated_at'
        ]
        read_only_fields = ['numero_servico', 'valor_final', 'created_at', 'updated_at']
    
    def get_duracao_real(self, obj):
        if obj.data_realizacao and obj.data_agendamento:
            delta = obj.data_realizacao - obj.data_agendamento
            return int(delta.total_seconds() / 60)  # em minutos
        return None
    
    def get_tempo_desde_agendamento(self, obj):
        from django.utils import timezone
        if obj.data_agendamento:
            delta = timezone.now() - obj.data_agendamento
            horas = int(delta.total_seconds() / 3600)
            if horas < 24:
                return f"{horas}h"
            else:
                dias = int(horas / 24)
                return f"{dias}d"
        return None
    
    def get_pode_ser_iniciado(self, obj):
        return obj.status == 'agendado'
    
    def get_pode_ser_finalizado(self, obj):
        return obj.status == 'em_andamento'
    
    def validate(self, data):
        # Validar se farmacêutico é obrigatório
        if data.get('servico') and data['servico'].requer_farmaceutico:
            if not data.get('farmaceutico'):
                raise serializers.ValidationError(
                    'Farmacêutico é obrigatório para este tipo de serviço'
                )
        
        # Validar desconto
        if data.get('desconto', 0) > data.get('preco_servico', 0):
            raise serializers.ValidationError(
                'Desconto não pode ser maior que o preço do serviço'
            )
        
        return data
    
    def create(self, validated_data):
        # Calcular valor final
        preco = validated_data.get('preco_servico', 0)
        desconto = validated_data.get('desconto', 0)
        validated_data['valor_final'] = preco - desconto
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Recalcular valor final se preço ou desconto mudaram
        if 'preco_servico' in validated_data or 'desconto' in validated_data:
            preco = validated_data.get('preco_servico', instance.preco_servico)
            desconto = validated_data.get('desconto', instance.desconto)
            validated_data['valor_final'] = preco - desconto
        
        return super().update(instance, validated_data)

# Serializers para listas resumidas
class ServicoResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para listas"""
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    paciente_nome = serializers.CharField(source='paciente.cliente.nome_completo', read_only=True)
    farmaceutico_nome = serializers.CharField(source='farmaceutico.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Servico
        fields = [
            'id', 'numero_servico', 'servico_nome', 'paciente_nome',
            'farmaceutico_nome', 'data_agendamento', 'status', 'status_display',
            'valor_final'
        ]


# apps/comandas/api/serializers.py
from rest_framework import serializers
from ..models import (
    Comanda, ItemComanda, ProdutoComanda, CategoriaComanda,
    Mesa, Pagamento, CentroRequisicao, TemplateComanda,
    MovimentacaoComanda, ConfiguracaoComanda
)

class CategoriaComandaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaComanda
        fields = ['id', 'nome', 'descricao', 'cor_exibicao', 'icone', 'ordem_exibicao', 'ativa']

class ProdutoComandaSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    preco_atual = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    em_promocao = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ProdutoComanda
        fields = [
            'id', 'codigo', 'nome', 'descricao', 'categoria', 'categoria_nome',
            'preco_venda', 'preco_promocional', 'preco_atual', 'em_promocao',
            'disponivel', 'destaque', 'tempo_preparo_minutos',
            'controla_estoque', 'quantidade_estoque', 'calorias', 'ingredientes'
        ]

class MesaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Mesa
        fields = [
            'id', 'numero', 'nome', 'capacidade', 'localizacao',
            'status', 'status_display', 'qr_code', 'ativa'
        ]

class ItemComandaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tempo_preparo = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemComanda
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade', 'preco_unitario',
            'total', 'status', 'status_display', 'observacoes',
            'hora_pedido', 'hora_inicio_preparo', 'hora_finalizacao',
            'hora_entrega', 'tempo_preparo'
        ]
        read_only_fields = ['total', 'hora_pedido']
    
    def get_tempo_preparo(self, obj):
        if obj.hora_inicio_preparo and obj.hora_finalizacao:
            delta = obj.hora_finalizacao - obj.hora_inicio_preparo
            return int(delta.total_seconds() / 60)  # em minutos
        return None

class PagamentoSerializer(serializers.ModelSerializer):
    forma_pagamento_display = serializers.CharField(source='get_forma_pagamento_display', read_only=True)
    
    class Meta:
        model = Pagamento
        fields = [
            'id', 'forma_pagamento', 'forma_pagamento_display', 'valor',
            'numero_transacao', 'numero_autorizacao', 'bandeira_cartao',
            'data_pagamento', 'confirmado', 'observacoes'
        ]
        read_only_fields = ['data_pagamento']

class ComandaSerializer(serializers.ModelSerializer):
    itens = ItemComandaSerializer(many=True, read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    atendente_nome = serializers.CharField(source='atendente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_atendimento_display = serializers.CharField(source='get_tipo_atendimento_display', read_only=True)
    total_itens = serializers.IntegerField(read_only=True)
    troco = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tempo_decorrido = serializers.SerializerMethodField()
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'tipo_atendimento', 'tipo_atendimento_display',
            'cliente', 'cliente_nome', 'mesa', 'mesa_numero', 'atendente', 'atendente_nome',
            'data_abertura', 'data_fechamento', 'tempo_estimado_preparo',
            'subtotal', 'desconto_valor', 'desconto_percentual', 'taxa_servico',
            'taxa_entrega', 'total', 'valor_pago', 'troco',
            'status', 'status_display', 'observacoes', 'observacoes_cozinha',
            'endereco_entrega', 'telefone_contato', 'total_itens',
            'tempo_decorrido', 'itens', 'pagamentos'
        ]
        read_only_fields = [
            'numero_comanda', 'data_abertura', 'subtotal', 'total',
            'tempo_estimado_preparo', 'total_itens', 'troco'
        ]
    
    def get_tempo_decorrido(self, obj):
        if obj.tempo_decorrido:
            return int(obj.tempo_decorrido.total_seconds() / 60)  # em minutos
        return 0

class ComandaResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagens"""
    mesa_numero = serializers.CharField(source='mesa.numero', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_itens = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Comanda
        fields = [
            'id', 'numero_comanda', 'status', 'status_display',
            'cliente_nome', 'mesa_numero', 'total', 'total_itens',
            'data_abertura'
        ]

class CentroRequisicaoSerializer(serializers.ModelSerializer):
    tipo_centro_display = serializers.CharField(source='get_tipo_centro_display', read_only=True)
    esta_funcionando = serializers.BooleanField(read_only=True)
    itens_pendentes = serializers.SerializerMethodField()
    
    class Meta:
        model = CentroRequisicao
        fields = [
            'id', 'codigo', 'nome', 'tipo_centro', 'tipo_centro_display',
            'descricao', 'localizacao', 'responsavel', 'ativo',
            'aceita_pedidos', 'horario_inicio', 'horario_fim',
            'esta_funcionando', 'itens_pendentes'
        ]
    
    def get_itens_pendentes(self, obj):
        return obj.itens_pendentes_count()

class MovimentacaoComandaSerializer(serializers.ModelSerializer):
    tipo_movimentacao_display = serializers.CharField(source='get_tipo_movimentacao_display', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    
    class Meta:
        model = MovimentacaoComanda
        fields = [
            'id', 'tipo_movimentacao', 'tipo_movimentacao_display', 'descricao',
            'valor_anterior', 'valor_atual', 'valor_alteracao',
            'usuario', 'usuario_nome', 'data_movimentacao'
        ]
        read_only_fields = ['data_movimentacao']


