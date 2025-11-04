from rest_framework import serializers
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import TaxaIVAAGT, AssinaturaDigital, RetencaoFonte
from apps.fornecedores.models import Fornecedor
from apps.financeiro.models import ContaPagar

class TaxaIVAAGTSerializer(serializers.ModelSerializer):
    """
    Serializer para TaxaIVAAGT com validações SAF-T AO v1.01
    """
    
    # Campos calculados/somente leitura
    nome_completo = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tax_type_display', read_only=True)
    codigo_display = serializers.CharField(source='get_tax_code_display', read_only=True)
    isencao_display = serializers.CharField(source='get_exemption_reason_display', read_only=True)
    
    # Validações customizadas
    tax_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False,
        help_text="Taxa em percentual (ex: 14.00 para 14%)"
    )
    
    class Meta:
        model = TaxaIVAAGT
        fields = [
            'id', 'nome', 'codigo_pais', 'tax_type', 'tax_code',
            'tax_percentage', 'exemption_reason', 'legislacao_referencia',
            'ativo', 'created_at', 'updated_at',
            # Campos calculados
            'nome_completo', 'tipo_display', 'codigo_display', 'isencao_display'
        ]
        read_only_fields = ['id', 'codigo_pais', 'created_at', 'updated_at']
    
    def get_nome_completo(self, obj):
        """Retorna nome completo com percentual ou tipo de isenção"""
        if obj.tax_type == 'IVA':
            return f"{obj.nome} ({obj.tax_percentage}%)"
        elif obj.exemption_reason:
            return f"{obj.nome} ({obj.exemption_reason})"
        return obj.nome
    
    def validate(self, data):
        """Validações SAF-T específicas"""
        tax_type = data.get('tax_type')
        tax_percentage = data.get('tax_percentage')
        exemption_reason = data.get('exemption_reason')
        
        # Se for IVA, deve ter tax_percentage
        if tax_type == 'IVA':
            if not tax_percentage or tax_percentage < 0:
                raise serializers.ValidationError({
                    'tax_percentage': 'IVA deve ter uma taxa percentual válida maior ou igual a 0'
                })
            if tax_percentage > 100:
                raise serializers.ValidationError({
                    'tax_percentage': 'Taxa percentual não pode ser maior que 100%'
                })
            # Limpar exemption_reason se for IVA
            data['exemption_reason'] = None
        
        # Se for IS ou NS, deve ter exemption_reason
        elif tax_type in ['IS', 'NS']:
            if not exemption_reason:
                raise serializers.ValidationError({
                    'exemption_reason': f'{tax_type} deve ter um código de isenção válido'
                })
            # Limpar tax_percentage se for isenção
            data['tax_percentage'] = Decimal('0.00')
        
        return data
    
    def validate_nome(self, value):
        """Valida se o nome não está duplicado na empresa"""
        empresa = self.context['request'].user.empresa_ativa
        queryset = TaxaIVAAGT.objects.filter(empresa=empresa, nome=value)
        
        # Se estiver editando, excluir o objeto atual
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe uma taxa com este nome na empresa"
            )
        
        return value
    
    def validate_tax_code(self, value):
        """Valida códigos SAF-T permitidos"""
        codigos_validos = ['NOR', 'INT', 'RED', 'ISE', 'NSU']
        if value not in codigos_validos:
            raise serializers.ValidationError(
                f"Código deve ser um dos seguintes: {', '.join(codigos_validos)}"
            )
        return value
    
    def to_representation(self, instance):
        """Customiza a representação dos dados"""
        data = super().to_representation(instance)
        
        # Formatar tax_percentage para display
        if data['tax_percentage']:
            data['tax_percentage_formatted'] = f"{float(data['tax_percentage']):.2f}%"
        else:
            data['tax_percentage_formatted'] = "N/A"
        
        # Adicionar informações SAF-T
        data['saft_compliant'] = True
        data['country_code'] = 'AO'
        
        return data


class AssinaturaDigitalSerializer(serializers.ModelSerializer):
    """
    Serializer para AssinaturaDigital com campos sensíveis protegidos
    """
    
    # Campos calculados
    configurada = serializers.SerializerMethodField()
    total_series = serializers.SerializerMethodField()
    ultimo_hash_resumo = serializers.SerializerMethodField()
    chave_publica_resumo = serializers.SerializerMethodField()
    
    # Campos protegidos (não retornar chave privada)
    chave_privada = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AssinaturaDigital
        fields = [
            'id', 'ultimo_hash', 'chave_publica', 'chave_privada',
            'dados_series_fiscais', 'data_geracao', 'created_at', 'updated_at',
            # Campos calculados
            'configurada', 'total_series', 'ultimo_hash_resumo', 'chave_publica_resumo'
        ]
        read_only_fields = [
            'id', 'ultimo_hash', 'dados_series_fiscais', 'data_geracao',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'chave_publica': {'write_only': True},
            'ultimo_hash': {'help_text': 'Hash do último documento na cadeia de integridade'}
        }
    
    def get_configurada(self, obj):
        """Verifica se a assinatura está configurada"""
        return bool(obj.chave_publica and obj.chave_privada)
    
    def get_total_series(self, obj):
        """Retorna total de séries fiscais configuradas"""
        return len(obj.dados_series_fiscais) if obj.dados_series_fiscais else 0
    
    def get_ultimo_hash_resumo(self, obj):
        """Retorna resumo do último hash (primeiros 20 caracteres)"""
        if obj.ultimo_hash:
            return f"{obj.ultimo_hash[:20]}..."
        return None
    
    def get_chave_publica_resumo(self, obj):
        """Retorna resumo da chave pública"""
        if obj.chave_publica:
            linhas = obj.chave_publica.split('\n')
            if len(linhas) > 2:
                return f"{linhas[0]}...{linhas[-2]}"
        return None
    
    def to_representation(self, instance):
        """Customiza representação para proteger dados sensíveis"""
        data = super().to_representation(instance)
        
        # Adicionar informações das séries fiscais sem dados sensíveis
        if instance.dados_series_fiscais:
            series_info = {}
            for serie, dados in instance.dados_series_fiscais.items():
                series_info[serie] = {
                    'ultimo_documento': dados.get('ultimo_documento'),
                    'data_ultima_assinatura': dados.get('data_ultima_assinatura'),
                    'hash_configurado': bool(dados.get('ultimo_hash'))
                }
            data['series_fiscais_info'] = series_info
        
        return data


class RetencaoFonteSerializer(serializers.ModelSerializer):
    """
    Serializer para RetencaoFonte com validações fiscais
    """
    
    # Campos de relacionamento expandidos
    fornecedor_nome = serializers.CharField(source='fornecedor.razao_social', read_only=True)
    fornecedor_nif = serializers.CharField(source='fornecedor.nif', read_only=True)
    conta_pagar_numero = serializers.CharField(source='conta_pagar.numero_documento', read_only=True)
    
    # Campos calculados
    tipo_retencao_display = serializers.CharField(source='get_tipo_retencao_display', read_only=True)
    valor_base_formatado = serializers.SerializerMethodField()
    valor_retido_formatado = serializers.SerializerMethodField()
    taxa_retencao_formatado = serializers.SerializerMethodField()
    status_pagamento = serializers.SerializerMethodField()
    
    # Validações customizadas
    valor_base = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Base tributável para cálculo da retenção"
    )
    taxa_retencao = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Taxa de retenção em percentual (ex: 6.5 para 6,5%)"
    )
    valor_retido = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True,
        help_text="Valor calculado automaticamente"
    )
    
    # Campos de relacionamento com validação
    fornecedor = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(),
        help_text="Fornecedor ao qual foi efetuada a retenção"
    )
    conta_pagar = serializers.PrimaryKeyRelatedField(
        queryset=ContaPagar.objects.all(),
        required=False,
        allow_null=True,
        help_text="Conta a pagar que gerou esta retenção (opcional)"
    )
    
    class Meta:
        model = RetencaoFonte
        fields = [
            'id', 'referencia_documento', 'data_retencao', 'valor_base',
            'taxa_retencao', 'valor_retido', 'tipo_retencao', 'codigo_tributario',
            'conta_pagar', 'fornecedor', 'paga_ao_estado', 'created_at', 'updated_at',
            # Campos expandidos
            'fornecedor_nome', 'fornecedor_nif', 'conta_pagar_numero',
            # Campos calculados
            'tipo_retencao_display', 'valor_base_formatado', 'valor_retido_formatado',
            'taxa_retencao_formatado', 'status_pagamento'
        ]
        read_only_fields = ['id', 'valor_retido', 'created_at', 'updated_at']
    
    def get_valor_base_formatado(self, obj):
        """Formata valor base para exibição"""
        return f"AKZ {obj.valor_base:,.2f}"
    
    def get_valor_retido_formatado(self, obj):
        """Formata valor retido para exibição"""
        return f"AKZ {obj.valor_retido:,.2f}"
    
    def get_taxa_retencao_formatado(self, obj):
        """Formata taxa de retenção para exibição"""
        return f"{obj.taxa_retencao}%"
    
    def get_status_pagamento(self, obj):
        """Retorna status do pagamento ao Estado"""
        return "Pago" if obj.paga_ao_estado else "Pendente"
    
    def validate_taxa_retencao(self, value):
        """Valida se a taxa está dentro dos limites permitidos"""
        if value < 0:
            raise serializers.ValidationError("Taxa de retenção não pode ser negativa")
        if value > 100:
            raise serializers.ValidationError("Taxa de retenção não pode ser maior que 100%")
        return value
    
    def validate_valor_base(self, value):
        """Valida se o valor base é positivo"""
        if value <= 0:
            raise serializers.ValidationError("Valor base deve ser maior que zero")
        return value
    
    def validate_data_retencao(self, value):
        """Valida se a data de retenção não é futura"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Data de retenção não pode ser futura")
        return value
    
    def validate_fornecedor(self, value):
        """Valida se o fornecedor pertence à empresa"""
        empresa = self.context['request'].user.empresa_ativa
        if value.empresa != empresa:
            raise serializers.ValidationError(
                "Fornecedor deve pertencer à empresa ativa"
            )
        return value
    
    def validate_conta_pagar(self, value):
        """Valida se a conta a pagar pertence à empresa"""
        if value:
            empresa = self.context['request'].user.empresa_ativa
            if value.empresa != empresa:
                raise serializers.ValidationError(
                    "Conta a pagar deve pertencer à empresa ativa"
                )
        return value
    
    def validate(self, data):
        """Validações cruzadas"""
        # Verificar se conta_pagar é do mesmo fornecedor
        conta_pagar = data.get('conta_pagar')
        fornecedor = data.get('fornecedor')
        
        if conta_pagar and fornecedor:
            if conta_pagar.fornecedor != fornecedor:
                raise serializers.ValidationError({
                    'conta_pagar': 'Conta a pagar deve ser do mesmo fornecedor selecionado'
                })
        
        return data
    
    def create(self, validated_data):
        """Criação com cálculo automático do valor retido"""
        # Calcular valor retido automaticamente
        valor_base = validated_data['valor_base']
        taxa_retencao = validated_data['taxa_retencao']
        valor_retido = valor_base * (taxa_retencao / Decimal('100.00'))
        validated_data['valor_retido'] = valor_retido
        
        # Adicionar empresa do usuário
        validated_data['empresa'] = self.context['request'].user.empresa_ativa
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Atualização com recálculo do valor retido se necessário"""
        # Se valor_base ou taxa_retencao mudaram, recalcular valor_retido
        valor_base = validated_data.get('valor_base', instance.valor_base)
        taxa_retencao = validated_data.get('taxa_retencao', instance.taxa_retencao)
        
        if 'valor_base' in validated_data or 'taxa_retencao' in validated_data:
            valor_retido = valor_base * (taxa_retencao / Decimal('100.00'))
            validated_data['valor_retido'] = valor_retido
        
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        """Customiza representação para adicionar informações SAF-T"""
        data = super().to_representation(instance)
        
        # Adicionar informações para SAF-T
        data['saft_info'] = {
            'tax_type': instance.tipo_retencao,
            'tax_country_region': 'AO',
            'tax_code': instance.codigo_tributario or 'N/A',
            'tax_percentage': float(instance.taxa_retencao),
            'withheld_amount': float(instance.valor_retido),
            'payment_status': 'Paid' if instance.paga_ao_estado else 'Pending'
        }
        
        # Adicionar dados de auditoria
        data['audit_info'] = {
            'created_date': instance.created_at.strftime('%Y-%m-%d'),
            'last_modified': instance.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'retention_reference': instance.referencia_documento
        }
        
        return data


# Serializers adicionais para relatórios e dashboards

class RetencaoFonteResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagens e relatórios
    """
    fornecedor_nome = serializers.CharField(source='fornecedor.razao_social', read_only=True)
    valor_retido_formatado = serializers.SerializerMethodField()
    status_pagamento = serializers.SerializerMethodField()
    
    class Meta:
        model = RetencaoFonte
        fields = [
            'id', 'referencia_documento', 'data_retencao', 'tipo_retencao',
            'valor_retido', 'paga_ao_estado', 'fornecedor_nome',
            'valor_retido_formatado', 'status_pagamento'
        ]
    
    def get_valor_retido_formatado(self, obj):
        return f"AKZ {obj.valor_retido:,.2f}"
    
    def get_status_pagamento(self, obj):
        return "Pago" if obj.paga_ao_estado else "Pendente"


class TaxaIVAResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para seleção de taxas
    """
    nome_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxaIVAAGT
        fields = ['id', 'nome', 'tax_type', 'tax_percentage', 'nome_completo']
    
    def get_nome_completo(self, obj):
        if obj.tax_type == 'IVA':
            return f"{obj.nome} ({obj.tax_percentage}%)"
        return f"{obj.nome} ({obj.tax_type})"

