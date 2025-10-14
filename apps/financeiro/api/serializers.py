# apps/financeiro/api/serializers.py
from rest_framework import serializers
from ..models import ContaReceber, ContaPagar, LancamentoFinanceiro, CategoriaFinanceira, CentroCusto

class CategoriaFinanceiraSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaFinanceira
        fields = '__all__'

class CentroCustoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCusto
        fields = '__all__'

class ContaReceberSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    dias_atraso = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ContaReceber
        fields = '__all__'

class ContaPagarSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    dias_atraso = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ContaPagar
        fields = '__all__'

class LancamentoFinanceiroSerializer(serializers.ModelSerializer):
    criado_por_nome = serializers.CharField(
        source='criado_por.nome', 
        read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display', 
        read_only=True
    )
    valor_formatado = serializers.SerializerMethodField()
    
    class Meta:
        model = LancamentoFinanceiro
        fields = [
            'id', 'descricao', 'valor', 'valor_formatado', 'tipo', 
            'tipo_display', 'data', 'criado_por', 'criado_por_nome'
        ]
        read_only_fields = ['criado_por']
    
    def get_valor_formatado(self, obj):
        """Retorna valor formatado como moeda"""
        return f"R$ {obj.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def validate_valor(self, value):
        """Valida se o valor é positivo"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value
    
    def validate_data(self, value):
        """Valida se a data não é muito antiga ou futura"""
        from datetime import date, timedelta
        
        hoje = date.today()
        limite_passado = hoje - timedelta(days=365 * 2)  # 2 anos atrás
        limite_futuro = hoje + timedelta(days=365)       # 1 ano à frente
        
        if value < limite_passado:
            raise serializers.ValidationError("Data não pode ser anterior a 2 anos")
        
        if value > limite_futuro:
            raise serializers.ValidationError("Data não pode ser superior a 1 ano à frente")
        
        return value

class CategoriaFinanceiraSerializer(serializers.ModelSerializer):
    total_uso = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoriaFinanceira
        fields = ['id', 'nome', 'descricao', 'total_uso']
    
    def get_total_uso(self, obj):
        """Retorna total de uso da categoria"""
        # Implementar quando houver relacionamento com lançamentos
        return 0
    
    def validate_nome(self, value):
        """Valida nome da categoria"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Nome deve ter pelo menos 2 caracteres")
        
        # Verificar duplicatas (case insensitive)
        if self.instance:
            # Atualizando categoria existente
            existe = CategoriaFinanceira.objects.filter(
                nome__iexact=value.strip()
            ).exclude(id=self.instance.id).exists()
        else:
            # Criando nova categoria
            existe = CategoriaFinanceira.objects.filter(
                nome__iexact=value.strip()
            ).exists()
        
        if existe:
            raise serializers.ValidationError("Já existe uma categoria com este nome")
        
        return value.strip().title()
    
    def validate_descricao(self, value):
        """Valida descrição da categoria"""
        if value and len(value.strip()) > 500:
            raise serializers.ValidationError("Descrição não pode ter mais de 500 caracteres")
        
        return value.strip() if value else None

class LancamentoResumoSerializer(serializers.Serializer):
    """Serializer para resumo de lançamentos"""
    periodo = serializers.CharField()
    total_entradas = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_saidas = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantidade_total = serializers.IntegerField()

class CategoriaEstatisticasSerializer(serializers.Serializer):
    """Serializer para estatísticas de categorias"""
    total_categorias = serializers.IntegerField()
    com_descricao = serializers.IntegerField()
    sem_descricao = serializers.IntegerField()
    percentual_com_descricao = serializers.DecimalField(max_digits=5, decimal_places=2)


