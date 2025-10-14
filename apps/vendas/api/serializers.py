# apps/vendas/api/serializers.py
from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from apps.produtos.models import Produto


from ..models import Venda, ItemVenda, PagamentoVenda, DevolucaoVenda

class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome_comercial', read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    # Campos que o frontend enviará
    produto_id = serializers.IntegerField(write_only=True)
    
    # Campos que serão preenchidos automaticamente/calculados
    iva_percentual = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2) 
    
    class Meta:
        model = ItemVenda
        fields = '__all__'
        read_only_fields = ['subtotal_sem_iva', 'iva_valor', 'total']
    
    def validate_produto_id(self, value):
        try:
            produto = Produto.objects.get(pk=value)
            # Armazena o objeto Produto para uso no validate/create
            self.produto_obj = produto
        except Produto.DoesNotExist:
            raise serializers.ValidationError("Produto não encontrado.")
        return value
        
    def to_internal_value(self, data):
        """Calcula os totais e impostos do item antes da validação da Venda."""
        # A lógica de cálculo deve ser rigorosa aqui:
        
        internal_data = super().to_internal_value(data)
        produto = getattr(self, 'produto_obj', None)
        
        if produto:
            quantidade = internal_data.get('quantidade', Decimal('1'))
            preco_unitario = internal_data.get('preco_unitario', Decimal('0'))
            desconto_item = internal_data.get('desconto_item', Decimal('0'))
            
            # 1. Obter a Taxa Fiscal AGT
            iva_percentual_agt = produto.iva_percentual # FK TaxaIVAAGT do modelo Produto
            if not iva_percentual_agt:
                 raise serializers.ValidationError("Produto não tem taxa de IVA legal associada.")
            
            # 2. Cálculos Base
            subtotal_bruto = quantidade * preco_unitario
            valor_liquido_item = subtotal_bruto - desconto_item
            
            # 3. Cálculo do IVA
            taxa_percentual = iva_percentual_agt.tax_percentage / Decimal('100.00')
            iva_valor = valor_liquido_item * taxa_percentual
            total_item = valor_liquido_item + iva_valor
            
            # 4. Inserir dados fiscais e calculados
            internal_data['produto'] = produto
            internal_data['iva_percentual'] = iva_percentual_agt
            internal_data['tax_type'] = iva_percentual_agt.tax_type
            internal_data['tax_code'] = iva_percentual_agt.tax_code
            internal_data['iva_valor'] = iva_valor.quantize(Decimal('0.01'))
            internal_data['subtotal_sem_iva'] = valor_liquido_item.quantize(Decimal('0.01'))
            internal_data['total'] = total_item.quantize(Decimal('0.01'))
            
        return internal_data


class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagamentoVenda
        fields = '__all__'


class VendaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ['numero_venda', 'created_at', 'updated_at', 'subtotal_sem_iva', 'iva_valor', 'total']
    
    def validate(self, data):
        """Validações de negócio e pré-cálculo dos totais da fatura."""
        itens_data = data.get('itens', [])
        if not itens_data:
            raise serializers.ValidationError({'itens': 'Uma venda deve ter pelo menos um item.'})
            
        total_venda = Decimal('0.00')
        iva_total = Decimal('0.00')
        subtotal_liquido = Decimal('0.00')

        # Soma os totais calculados no ItemVendaSerializer
        for item in itens_data:
            total_venda += item['total']
            iva_total += item['iva_valor']
            subtotal_liquido += item['subtotal_sem_iva']
            
        # O total deve ser sempre o campo CRÍTICO para o Hash e SAF-T
        data['total'] = total_venda.quantize(Decimal('0.01'))
        data['iva_valor'] = iva_total.quantize(Decimal('0.01'))
        data['subtotal'] = subtotal_liquido.quantize(Decimal('0.01')) # Mantendo o nome existente

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Cria a Venda e as Linhas, e então executa a assinatura fiscal crítica."""
        itens_data = validated_data.pop('itens')

        # 1. Criação da Venda (Status: Pendente ou Preparação)
        # Salvamos inicialmente sem o hash/numero_venda para entrar na lógica do service
        venda = Venda.objects.create(**validated_data)
        
        # 2. Criação das Linhas da Venda
        item_vendas = []
        for item_data in itens_data:
            produto = item_data.pop('produto')
            iva_percentual = item_data.pop('iva_percentual')
            
            # Usa os campos de 'ItemVenda' já calculados e os objetos FK
            item = ItemVenda(
                venda=venda, 
                produto=produto, 
                iva_percentual=iva_percentual,
                nome_produto=produto.nome, # Cache do nome
                **item_data
            )
            item_vendas.append(item)
            
        ItemVenda.objects.bulk_create(item_vendas)

        # 3. Assinatura e Finalização (Chamada Crítica ao Service Fiscal)
        try:
            # O service irá gerar numero_venda, hash_documento e atcud
            venda.status = 'finalizada'
            venda.assinar_e_finalizar() 
            
        except Exception as e:
            # Se a assinatura falhar, a transação atómica é revertida, 
            # garantindo que não há documentos não assinados/numerados no BD.
            raise serializers.ValidationError(f"Erro CRÍTICO no processo de assinatura fiscal: {e}")

        return venda

class DevolucaoSerializer(serializers.ModelSerializer):
    venda_numero = serializers.CharField(source='venda.numero_venda', read_only=True)
    
    class Meta:
        model = DevolucaoVenda
        fields = '__all__'

# apps/vendas/serializers.py (ADICIONE ISTO)
from rest_framework import serializers

class RentabilidadeItemSerializer(serializers.Serializer):
    """
    Define a estrutura de dados agregados de rentabilidade por produto/período.
    """
    # Dados de identificação/agrupamento
    produto_id = serializers.IntegerField()
    produto_nome = serializers.CharField()
    
    # Métricas de Volume
    total_vendido = serializers.DecimalField(max_digits=15, decimal_places=2)
    quantidade_total = serializers.DecimalField(max_digits=10, decimal_places=2)

    # Métricas de Lucro (Chave para o B.I.)
    custo_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    margem_bruta = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentual_margem_bruta = serializers.DecimalField(max_digits=5, decimal_places=2)
    
   