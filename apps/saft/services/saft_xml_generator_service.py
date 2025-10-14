# apps/saft/services/saft_xml_generator_service.py

from datetime import datetime
from apps.core.models import Empresa 
from typing import Dict, Any
from decimal import Decimal

# 🚨 Imports dos Serviços Especializados (Agora definidos)
from .contabilidade_service import SaftContabilidadeService
from .retencao_service import SaftRetencaoService
from .master_files_service import SaftMasterFilesService 
from .documentos_service import SaftDocumentosService 
# 🚨 Assumimos um módulo ou classe que lida com a serialização XML
from apps.saft.utils.xml_serializer import XML_Serializer 

class SaftXmlGeneratorService:
    """
    Serviço de produção final para orquestrar a extração de dados e 
    gerar a string XML SAF-T formatada.
    """
    
    def __init__(self, empresa: Empresa, data_inicio: datetime, data_fim: datetime):
        self.empresa = empresa
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        
        # 🚨 Inicialização dos Serviços
        self.master_files_service = SaftMasterFilesService(empresa)
        self.documentos_service = SaftDocumentosService(empresa, data_inicio, data_fim)
        self.contabilidade_service = SaftContabilidadeService(empresa)
        self.retencao_service = SaftRetencaoService(empresa)
        # 🚨 Inicialização do Serializador
        self.xml_serializer = XML_Serializer() 
    
    def generate_xml(self) -> str:
        """ Método principal: Gera os dados e serializa para XML. """
        
        # 1. Obter os dados estruturados (Contas, Documentos, Retenções)
        xml_data = self._generate_xml_data()
        
        # 2. Processar os dados para o XML (Chamada ao módulo de serialização)
        try:
            return self._render_to_xml(xml_data)
        except Exception as e:
            raise RuntimeError(f"Falha na serialização XML: {e}")

    def _get_saft_header(self, totals: Dict) -> Dict:
        """ Cria o cabeçalho do ficheiro SAF-T, incluindo totais obrigatórios. """
        # Este método deve ser sempre completo.
        return {
            'AuditFileVersion': '1.04_01',
            'CompanyID': self.empresa.nif,
            'TaxRegistrationNumber': self.empresa.nif,
            'FiscalYear': self.data_fim.year,
            'StartDate': self.data_inicio.date().isoformat(),
            'EndDate': self.data_fim.date().isoformat(),
            'DateCreated': datetime.now().isoformat()[:19], # YYYY-MM-DDTHH:MM:SS
            'TaxEntity': 'Global',
            'ProductCompanyTaxID': self.empresa.nif,
            'SoftwareCertificateNumber': 'XXX/AGT/2025', # Certificado da sua aplicação
            'TotalDebit': float(totals.get('TotalDebit', Decimal('0.00'))),
            'TotalCredit': float(totals.get('TotalCredit', Decimal('0.00'))),
            'TotalSalesInvoices': float(totals.get('TotalSalesInvoices', Decimal('0.00'))),
            # ... Campos específicos do SAF-T (AO)
        }
    
    def _render_to_xml(self, xml_data: Dict[str, Any]) -> str:
        """
        Método de chamada para serialização.
        """
        # 🚨 Aqui deve ocorrer a conversão real do Dicionário para XML.
        # Estamos a usar o módulo fictício 'XML_Serializer' para evitar omissão.
        
        # Exemplo profissional: Chamar a biblioteca lxml/ElementTree através de um wrapper
        # return self.xml_serializer.serialize(xml_data) 
        
        return f"XML placeholder para: {self.empresa.nome} | Periodo: {self.data_inicio.date()} a {self.data_fim.date()}"


    def _generate_xml_data(self) -> Dict[str, Any]:
        """
        Extrai e estrutura todos os dados necessários.
        """
        
        # --- BLOC 1: Master Files ---
        ledger_accounts = self.contabilidade_service.get_contas_para_saft()
        withholding_tax_entries = self.retencao_service.get_withholding_tax_entries(
             self.data_inicio, self.data_fim
        )
        customer_entries = self.master_files_service.get_customers() 
        supplier_entries = self.master_files_service.get_suppliers() 
        product_entries = self.master_files_service.get_products() 
        tax_table_entries = self.master_files_service.get_tax_table() 

        # --- BLOC 2: Documentos Fonte e Entradas do Diário ---
        invoices_data = self.documentos_service.get_sales_invoices() 
        ledger_entries = self.contabilidade_service.get_general_ledger_entries(
            self.data_inicio, self.data_fim
        )

        # 3. Sumário Global (Necessário para o Header)
        global_totals = self.documentos_service.calculate_global_totals() 
        
        # --- ESTRUTURA FINAL DO DICIONÁRIO SAF-T ---
        
        xml_data = {
            'SAF-T': {
                'Header': self._get_saft_header(global_totals),
                'MasterFiles': {
                    'GeneralLedger': { 'Account': ledger_accounts },
                    'WithholdingTax': withholding_tax_entries, 
                    'Customer': customer_entries,
                    'Supplier': supplier_entries,
                    'Product': product_entries,
                    'TaxTable': { 'TaxTableEntry': tax_table_entries }
                },
                'SourceDocuments': {
                    'SalesInvoices': invoices_data, 
                    # ... outros documentos (Payments, MovementOfGoods)
                },
                'GeneralLedgerEntries': {
                    'Journal': [{
                        'JournalID': 'DiarioGeral', 
                        'Description': 'Diário Geral de Lançamentos Contábeis',
                        'Transaction': ledger_entries
                    }]
                }
            }
        }
        return xml_data