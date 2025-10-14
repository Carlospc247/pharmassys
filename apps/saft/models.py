# apps/saft/services.py

from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
from django.db.models import Sum
from django.db import models
from apps.clientes.models import Cliente
from apps.core.models import Empresa
from apps.produtos.models import Produto
from apps.vendas.models import Venda

# 🚨 IMPORTAÇÕES REQUERIDAS
# Ajuste as paths conforme a sua estrutura (e.g., core.models, vendas.models, etc.)
# from apps.core.models import Empresa
# from apps.vendas.models import Venda, ItemVenda
# from apps.clientes.models import Cliente
# from apps.produtos.models import Produto
# from apps.fiscais.models import TaxaIVAAGT 


# Namespace XML do SAF-T (Angola V1.01)
SAFT_NS = "urn:saf-t:ao:1.01" 
NS_MAP = {'xmlns': SAFT_NS} 

class SaftXmlGeneratorService:
    """
    Serviço rigoroso para a geração do ficheiro SAF-T (AO) XML.
    Garante o mapeamento completo e o formato do schema XML para submissão à AGT.
    """
    
    def __init__(self, empresa: Empresa, data_inicio: datetime, data_fim: datetime):
        self.empresa = empresa
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.root = ET.Element('AuditFile', NS_MAP) # Cria o elemento raiz
        
    # --- UTILS INTERNOS ---

    def _sub_element(self, parent, tag_name, text_content=None):
        """ Função utilitária para criar sub-elementos com o namespace correto. """
        element = ET.SubElement(parent, f"{{{SAFT_NS}}}{tag_name}")
        if text_content is not None:
            # Formatação de decimais para string (sempre com 2 casas e '.' como separador)
            if isinstance(text_content, Decimal):
                element.text = f"{text_content:.2f}"
            else:
                element.text = str(text_content)
        return element

    # --- BLOCos XML ---

    def _create_header(self):
        """ 4. Bloco de Cabeçalho (Header) """
        header = self._sub_element(self.root, 'Header')
        
        # 4.1. Versão e Empresa
        self._sub_element(header, 'AuditFileVersion', "1.01") 
        self._sub_element(header, 'CompanyID', self.empresa.nif)
        self._sub_element(header, 'TaxRegistrationNumber', self.empresa.nif)
        self._sub_element(header, 'CompanyName', self.empresa.nome)
        self._sub_element(header, 'FiscalYear', str(self.data_fim.year))
        self._sub_element(header, 'StartDate', self.data_inicio.strftime('%Y-%m-%d'))
        self._sub_element(header, 'EndDate', self.data_fim.strftime('%Y-%m-%d'))
        self._sub_element(header, 'DateCreated', datetime.now().strftime('%Y-%m-%d'))
        self._sub_element(header, 'TaxAccountingBasis', "F") # F - Faturação
        self._sub_element(header, 'CurrencyCode', "AOA") # Moeda: Kwanza Angolano
        
        # 4.2. Endereço da Empresa
        company_address = self._sub_element(header, 'CompanyAddress')
        self._sub_element(company_address, 'StreetName', self.empresa.endereco)
        self._sub_element(company_address, 'City', self.empresa.cidade)
        self._sub_element(company_address, 'PostalCode', self.empresa.postal)
        self._sub_element(company_address, 'Region', self.empresa.provincia)
        self._sub_element(company_address, 'Country', "AO") # AngoLa
        
    def _create_master_files(self, TaxaIVAAGT):
        """ 5. Bloco de Dados Mestre (MasterFiles) """
        master_files = self._sub_element(self.root, 'MasterFiles')

        # 5.1. Tabela de Impostos (TaxTable)
        tax_table = self._sub_element(master_files, 'TaxTable')
        
        # Assumindo que TaxaIVAAGT é um modelo Django com as taxas fiscais legais
        for taxa in TaxaIVAAGT.objects.all():
            tax_entry = self._sub_element(tax_table, 'TaxTableEntry')
            self._sub_element(tax_entry, 'TaxType', taxa.tax_type)        # Ex: IVA, IS, NS
            self._sub_element(tax_entry, 'TaxCode', taxa.tax_code)        # Ex: NOR, ISE, NSU
            self._sub_element(tax_entry, 'Description', taxa.descricao)   # Ex: IVA - Normal
            self._sub_element(tax_entry, 'TaxCountryRegion', taxa.tax_country) # Ex: AO
            self. _sub_element(tax_entry, 'TaxPercentage', taxa.tax_percentage) # Ex: 14.00

        # 5.2. Clientes (Customer)
        customers = self._sub_element(master_files, 'Customer')
        # Filtra apenas os clientes ativos ou que fizeram vendas no período
        for cliente in Cliente.objects.filter(empresa=self.empresa):
            customer = self._sub_element(customers, 'Customer')
            self._sub_element(customer, 'CustomerID', cliente.codigo_cliente) # Código interno
            self._sub_element(customer, 'CustomerTaxID', cliente.nif or '999999999') # 9999... para consumidor final
            self._sub_element(customer, 'CompanyName', cliente.nome_exibicao)
            self._sub_element(customer, 'SelfBillingIndicator', 0) # 0 - Sem Autofacturação

            customer_address = self._sub_element(customer, 'BillingAddress')
            self._sub_element(customer_address, 'StreetName', cliente.endereco or 'N/A')
            self._sub_element(customer_address, 'City', cliente.cidade or 'N/A')
            self._sub_element(customer_address, 'PostalCode', cliente.postal or 'N/A')
            self._sub_element(customer_address, 'Country', "AO") 
            
        # 5.3. Produtos/Serviços (Product)
        products = self._sub_element(master_files, 'Product')
        for produto in Produto.objects.filter(empresa=self.empresa):
            product = self._sub_element(products, 'Product')
            self._sub_element(product, 'ProductType', produto.tipo_produto) # M (Mercadoria) ou S (Serviço)
            self._sub_element(product, 'ProductCode', produto.codigo_interno)
            self._sub_element(product, 'ProductDescription', produto.nome_produto)
            self._sub_element(product, 'ProductNumberCode', produto.codigo_barras) # PODE ser o código de barras ou interno

    def _create_sales_invoices(self):
        """ 6. Bloco de Documentos de Faturação (SalesInvoices) """
        sales_invoices = self._sub_element(self.root, 'SalesInvoices')
        
        vendas = Venda.objects.filter(
            empresa=self.empresa,
            data_venda__range=[self.data_inicio, self.data_fim],
            status='finalizada' # Apenas documentos finalizados
        ).select_related('cliente', 'forma_pagamento').prefetch_related('itens')
        
        ET.SubElement(sales_invoices, f"{{{SAFT_NS}}}NumberOfEntries").text = str(vendas.count())
        
        # CÁLCULO DE TOTAIS GERAIS (Obrigatório)
        totals = vendas.aggregate(
            total_bruto=Sum('subtotal'),
            total_desconto=Sum('desconto_valor'),
            total_imposto=Sum('iva_valor'),
            total_liquido=Sum('total')
        )
        self._sub_element(sales_invoices, 'TotalDebit', totals['total_liquido'] or Decimal('0.00'))
        self._sub_element(sales_invoices, 'TotalCredit', totals['total_liquido'] or Decimal('0.00'))


        for venda in vendas:
            invoice = self._sub_element(sales_invoices, 'Invoice')
            
            # 6.1. Dados do Documento
            self._sub_element(invoice, 'InvoiceNo', venda.numero_venda)
            self._sub_element(invoice, 'DocumentStatus', 'N') # N - Normal
            self._sub_element(invoice, 'HashControl', '1') # 1 - Assinado por software certificado
            self._sub_element(invoice, 'Hash', venda.hash_documento) # 🚨 CAMPO CRÍTICO
            self._sub_element(invoice, 'ATUD', venda.atcud) # 🚨 CAMPO CRÍTICO
            self._sub_element(invoice, 'InvoiceDate', venda.data_venda.strftime('%Y-%m-%d'))
            self._sub_element(invoice, 'InvoiceType', 'FT') # FT - Fatura (Ajuste conforme seus CHOICES)
            self._sub_element(invoice, 'SystemEntryDate', venda.data_venda.strftime('%Y-%m-%dT%H:%M:%S'))
            self._sub_element(invoice, 'CustomerID', venda.cliente.codigo_cliente)
            self._sub_element(invoice, 'SelfBillingIndicator', 0)
            
            # 6.2. Linhas do Documento (ItensVenda)
            for i, item in enumerate(venda.itens.all()):
                line = self._sub_element(invoice, 'Line')
                self._sub_element(line, 'LineNumber', i + 1)
                self._sub_element(line, 'ProductCode', item.produto.codigo_interno if item.produto else item.servico.codigo_interno)
                self._sub_element(line, 'Quantity', item.quantidade)
                self._sub_element(line, 'UnitOfMeasure', 'UN') # Assumimos 'UN' (Unidade)
                self._sub_element(line, 'UnitPrice', item.preco_unitario)
                self._sub_element(line, 'TaxBase', item.subtotal_sem_iva)
                self._sub_element(line, 'CreditAmount', item.total)
                self._sub_element(line, 'DebitAmount', item.total)
                self._sub_element(line, 'GrossTotal', item.total + item.iva_valor)
                self._sub_element(line, 'NetTotal', item.total)
                
                # Desconto (Discount)
                if item.desconto_item > Decimal('0.00'):
                    self._sub_element(line, 'Discount', item.desconto_item)

                # 6.2.1. Taxa de Imposto da Linha (Tax)
                tax = self._sub_element(line, 'Tax')
                self._sub_element(tax, 'TaxType', item.tax_type)
                self._sub_element(tax, 'TaxCountryRegion', "AO")
                self._sub_element(tax, 'TaxCode', item.tax_code)
                self._sub_element(tax, 'TaxPercentage', item.iva_percentual)
            
            # 6.3. Totais Finais
            document_totals = self._sub_element(invoice, 'DocumentTotals')
            self._sub_element(document_totals, 'TaxPayable', venda.iva_valor)
            self._sub_element(document_totals, 'NetTotal', venda.subtotal - venda.desconto_valor)
            self._sub_element(document_totals, 'GrossTotal', venda.total)

    # --- FUNÇÃO PRINCIPAL ---

    def generate_xml(self, TaxaIVAAGT) -> bytes:
        """ Função principal que orquestra a criação do ficheiro XML. """
        
        # 1. Orquestração da Estrutura
        self._create_header()
        self._create_master_files(TaxaIVAAGT)
        self._create_sales_invoices()
        
        # 2. Finalização e Formato (Pretty Print)
        ET.register_namespace('', SAFT_NS)
        
        # Usa o ElementTree para gerar uma string com indentação (mais legível)
        xml_string = ET.tostring(self.root, encoding='utf-8', xml_declaration=True)
        
        # Nota: O SAF-T exige encoding UTF-8
        return xml_string



# Modelo fictício, apenas para "ancorar" a permissão fiscal
class SaftFiscalControl(models.Model):
    """
    Modelo proxy/simples para definir as permissões fiscais de alto nível.
    Não precisa ser um objeto na base de dados.
    """
    class Meta:
        managed = False  # Indica que o Django não deve criar uma tabela para este modelo
        verbose_name = "Controlo Fiscal SAF-T"
        verbose_name_plural = "Controlo Fiscal SAF-T"
        permissions = [
            # 🚨 PERMISSÃO CRÍTICA: 
            # Código: 'export_saft'
            ('export_saft', 'Pode exportar o ficheiro SAF-T (Acesso a dados fiscais brutos)'),
        ]

