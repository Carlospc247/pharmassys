# apps/saft/utils/xml_serializer.py

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Union, List, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class XML_Serializer:
    """
    Serializador XML profissional para gerar arquivos SAF-T (Standard Audit File for Tax)
    compatíveis com as especificações da AGT (Administração Geral Tributária) de Angola.
    
    Características:
    - Suporte completo ao namespace SAF-T Angola v1.04_01
    - Formatação XML bem estruturada e indentada
    - Validação de tipos de dados
    - Tratamento de caracteres especiais
    - Compatibilidade com encoding UTF-8
    - Logs detalhados para debugging
    """
    
    # Namespace oficial do SAF-T Angola
    SAFT_NAMESPACE = "urn:OECD:StandardAuditFile-Tax:AO_1.04_01"
    SAFT_SCHEMA_LOCATION = "urn:OECD:StandardAuditFile-Tax:AO_1.04_01 file:SAFTAO1.04_01.xsd"
    
    def __init__(self):
        """Inicializa o serializador XML."""
        self.encoding = 'UTF-8'
        self.xml_version = '1.0'
        
    def serialize(self, xml_data: Dict[str, Any]) -> str:
        """
        Método principal para serializar dados Python para XML SAF-T.
        
        Args:
            xml_data: Dicionário com dados estruturados para SAF-T
            
        Returns:
            String XML formatada e válida
            
        Raises:
            RuntimeError: Em caso de erro na serialização
        """
        
        try:
            logger.info("Iniciando serialização XML SAF-T")
            
            # 1. Validação inicial dos dados
            self._validate_input_data(xml_data)
            
            # 2. Criar elemento raiz com namespace
            root = self._create_root_element()
            
            # 3. Serializar estrutura SAF-T
            if 'SAF-T' in xml_data:
                self._serialize_saft_structure(root, xml_data['SAF-T'])
            else:
                raise ValueError("Estrutura SAF-T não encontrada nos dados")
            
            # 4. Gerar string XML formatada
            xml_string = self._format_xml_output(root)
            
            logger.info(f"Serialização XML concluída. Tamanho: {len(xml_string)} caracteres")
            return xml_string
            
        except Exception as e:
            logger.error(f"Erro na serialização XML: {e}")
            raise RuntimeError(f"Falha na serialização XML SAF-T: {e}")
    
    def _validate_input_data(self, xml_data: Dict[str, Any]) -> None:
        """Valida a estrutura básica dos dados de entrada."""
        
        if not isinstance(xml_data, dict):
            raise TypeError("xml_data deve ser um dicionário")
            
        if 'SAF-T' not in xml_data:
            raise ValueError("xml_data deve conter a chave 'SAF-T'")
            
        saft_data = xml_data['SAF-T']
        
        # Validar seções obrigatórias
        required_sections = ['Header']
        for section in required_sections:
            if section not in saft_data:
                raise ValueError(f"Seção obrigatória ausente: {section}")
    
    def _create_root_element(self) -> ET.Element:
        """Cria o elemento raiz do XML com namespace adequado."""
        
        # Registrar namespace para evitar prefixos indesejados
        ET.register_namespace('', self.SAFT_NAMESPACE)
        
        # Criar elemento raiz
        root = ET.Element(
            f"{{{self.SAFT_NAMESPACE}}}AuditFile"
        )
        
        # Adicionar atributos do schema
        root.set(
            f"{{{ET._namespace_map['http://www.w3.org/2001/XMLSchema-instance']}}}schemaLocation",
            self.SAFT_SCHEMA_LOCATION
        )
        
        return root
    
    def _serialize_saft_structure(self, root: ET.Element, saft_data: Dict[str, Any]) -> None:
        """Serializa a estrutura principal do SAF-T."""
        
        # Ordem específica das seções SAF-T
        section_order = [
            'Header',
            'MasterFiles',
            'GeneralLedgerEntries',
            'SourceDocuments',
        ]
        
        for section_name in section_order:
            if section_name in saft_data:
                section_element = self._create_element(root, section_name)
                self._serialize_section(section_element, saft_data[section_name])
    
    def _serialize_section(self, parent: ET.Element, section_data: Any) -> None:
        """Serializa uma seção específica do SAF-T."""
        
        if isinstance(section_data, dict):
            # Tratar seções com estrutura de dicionário
            if parent.tag.endswith('Header'):
                self._serialize_header(parent, section_data)
            elif parent.tag.endswith('MasterFiles'):
                self._serialize_master_files(parent, section_data)
            elif parent.tag.endswith('GeneralLedgerEntries'):
                self._serialize_general_ledger_entries(parent, section_data)
            elif parent.tag.endswith('SourceDocuments'):
                self._serialize_source_documents(parent, section_data)
            else:
                # Serialização genérica para dicionários
                self._serialize_dict_generic(parent, section_data)
                
        elif isinstance(section_data, list):
            # Tratar listas de elementos
            for item in section_data:
                self._serialize_section(parent, item)
        else:
            # Tratar valores simples
            parent.text = self._format_value(section_data)
    
    def _serialize_header(self, parent: ET.Element, header_data: Dict[str, Any]) -> None:
        """Serializa a seção Header com ordem específica dos campos."""
        
        # Ordem específica dos campos do Header
        header_field_order = [
            'AuditFileVersion',
            'CompanyID', 
            'TaxRegistrationNumber',
            'TaxAccountingBasis',
            'CompanyName',
            'BusinessName',
            'CompanyAddress',
            'FiscalYear',
            'StartDate',
            'EndDate',
            'CurrencyCode',
            'DateCreated',
            'TimeCreated',
            'ProductID',
            'ProductVersion',
            'HeaderComment',
            'TaxEntity',
            'ProductCompanyTaxID',
            'SoftwareCertificateNumber',
            'ProductKey',
            'TotalDebit',
            'TotalCredit', 
            'TotalSalesInvoices',
            'NumberOfEntries'
        ]
        
        for field_name in header_field_order:
            if field_name in header_data:
                field_element = self._create_element(parent, field_name)
                
                # Tratamento especial para endereço da empresa
                if field_name == 'CompanyAddress':
                    self._serialize_company_address(field_element, header_data[field_name])
                else:
                    field_element.text = self._format_value(header_data[field_name])
    
    def _serialize_company_address(self, parent: ET.Element, address_data: Union[Dict, str]) -> None:
        """Serializa o endereço da empresa."""
        
        if isinstance(address_data, dict):
            address_fields = ['AddressDetail', 'City', 'PostalCode', 'Province', 'Country']
            for field in address_fields:
                if field in address_data:
                    field_element = self._create_element(parent, field)
                    field_element.text = self._format_value(address_data[field])
        else:
            # Se for string, usar como AddressDetail
            detail_element = self._create_element(parent, 'AddressDetail')
            detail_element.text = self._format_value(address_data)
    
    def _serialize_master_files(self, parent: ET.Element, master_data: Dict[str, Any]) -> None:
        """Serializa a seção MasterFiles."""
        
        # Ordem das subsections em MasterFiles
        masterfiles_sections = [
            'GeneralLedger',
            'WithholdingTax', 
            'Customer',
            'Supplier',
            'Product',
            'TaxTable'
        ]
        
        for section_name in masterfiles_sections:
            if section_name in master_data:
                section_element = self._create_element(parent, section_name)
                section_data = master_data[section_name]
                
                # Tratamento específico para cada subsection
                if section_name == 'GeneralLedger':
                    self._serialize_general_ledger_accounts(section_element, section_data)
                elif section_name == 'TaxTable':
                    self._serialize_tax_table(section_element, section_data)
                elif section_name in ['Customer', 'Supplier', 'Product']:
                    self._serialize_master_file_entities(section_element, section_data, section_name)
                else:
                    self._serialize_section(section_element, section_data)
    
    def _serialize_general_ledger_accounts(self, parent: ET.Element, ledger_data: Any) -> None:
        """Serializa as contas do razão geral."""
        
        if isinstance(ledger_data, dict) and 'Account' in ledger_data:
            accounts = ledger_data['Account']
            if isinstance(accounts, list):
                for account in accounts:
                    account_element = self._create_element(parent, 'Account')
                    self._serialize_dict_generic(account_element, account)
    
    def _serialize_tax_table(self, parent: ET.Element, tax_data: Any) -> None:
        """Serializa a tabela de impostos."""
        
        if isinstance(tax_data, dict) and 'TaxTableEntry' in tax_data:
            tax_entries = tax_data['TaxTableEntry']
            if isinstance(tax_entries, list):
                for entry in tax_entries:
                    entry_element = self._create_element(parent, 'TaxTableEntry')
                    self._serialize_dict_generic(entry_element, entry)
    
    def _serialize_master_file_entities(self, parent: ET.Element, entities_data: Any, entity_type: str) -> None:
        """Serializa entidades dos master files (clientes, fornecedores, produtos)."""
        
        if isinstance(entities_data, list):
            for entity in entities_data:
                entity_element = self._create_element(parent, entity_type)
                self._serialize_dict_generic(entity_element, entity)
    
    def _serialize_general_ledger_entries(self, parent: ET.Element, ledger_data: Dict[str, Any]) -> None:
        """Serializa lançamentos contábeis."""
        
        if 'Journal' in ledger_data:
            journals = ledger_data['Journal']
            if isinstance(journals, list):
                for journal in journals:
                    journal_element = self._create_element(parent, 'Journal')
                    self._serialize_journal(journal_element, journal)
    
    def _serialize_journal(self, parent: ET.Element, journal_data: Dict[str, Any]) -> None:
        """Serializa um diário contábil."""
        
        # Campos do cabeçalho do diário
        journal_fields = ['JournalID', 'Description']
        for field in journal_fields:
            if field in journal_data:
                field_element = self._create_element(parent, field)
                field_element.text = self._format_value(journal_data[field])
        
        # Transações do diário
        if 'Transaction' in journal_data:
            transactions = journal_data['Transaction']
            if isinstance(transactions, list):
                for transaction in transactions:
                    trans_element = self._create_element(parent, 'Transaction')
                    self._serialize_dict_generic(trans_element, transaction)
    
    def _serialize_source_documents(self, parent: ET.Element, source_data: Dict[str, Any]) -> None:
        """Serializa documentos fonte."""
        
        source_sections = [
            'SalesInvoices',
            'MovementOfGoods', 
            'WorkingDocuments',
            'Payments'
        ]
        
        for section_name in source_sections:
            if section_name in source_data:
                section_element = self._create_element(parent, section_name)
                self._serialize_section(section_element, source_data[section_name])
    
    def _serialize_dict_generic(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """Serialização genérica para dicionários."""
        
        for key, value in data.items():
            child_element = self._create_element(parent, key)
            
            if isinstance(value, dict):
                self._serialize_dict_generic(child_element, value)
            elif isinstance(value, list):
                # Para listas, criar múltiplos elementos com o mesmo nome
                parent.remove(child_element)  # Remove elemento criado
                for item in value:
                    item_element = self._create_element(parent, key)
                    if isinstance(item, dict):
                        self._serialize_dict_generic(item_element, item)
                    else:
                        item_element.text = self._format_value(item)
            else:
                child_element.text = self._format_value(value)
    
    def _create_element(self, parent: ET.Element, tag_name: str) -> ET.Element:
        """Cria um elemento XML com o namespace adequado."""
        
        # Remover caracteres inválidos do nome da tag
        clean_tag_name = self._clean_tag_name(tag_name)
        
        # Criar elemento com namespace
        full_tag_name = f"{{{self.SAFT_NAMESPACE}}}{clean_tag_name}"
        element = ET.SubElement(parent, full_tag_name)
        
        return element
    
    def _clean_tag_name(self, tag_name: str) -> str:
        """Remove caracteres inválidos dos nomes das tags."""
        
        # Substituir caracteres problemáticos
        replacements = {
            ' ': '',
            '-': '_', 
            '.': '_',
            ':': '_',
        }
        
        clean_name = tag_name
        for old, new in replacements.items():
            clean_name = clean_name.replace(old, new)
        
        # Garantir que começa com letra
        if clean_name and not clean_name[0].isalpha():
            clean_name = 'Field_' + clean_name
            
        return clean_name
    
    def _format_value(self, value: Any) -> str:
        """Formata valores para inclusão no XML."""
        
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float, Decimal)):
            return str(value)
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        else:
            # Escapar caracteres especiais XML
            return self._escape_xml_chars(str(value))
    
    def _escape_xml_chars(self, text: str) -> str:
        """Escapa caracteres especiais para XML."""
        
        # XML entities básicas
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;") 
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#39;")
        
        return text
    
    def _format_xml_output(self, root: ET.Element) -> str:
        """Formata a saída XML com indentação adequada."""
        
        try:
            # Converter para string bruta
            rough_string = ET.tostring(root, encoding='unicode')
            
            # Usar minidom para formatação elegante
            parsed = minidom.parseString(rough_string)
            
            # Gerar XML formatado
            formatted_xml = parsed.toprettyxml(
                indent="  ",
                encoding=None,  # Para retornar string ao invés de bytes
                newl='\n'
            )
            
            # Limpar linhas vazias extras
            lines = [line for line in formatted_xml.split('\n') if line.strip()]
            
            # Adicionar declaração XML personalizada
            xml_declaration = f'<?xml version="{self.xml_version}" encoding="{self.encoding}"?>'
            
            # Combinar declaração com conteúdo
            if lines and lines[0].startswith('<?xml'):
                lines[0] = xml_declaration
            else:
                lines.insert(0, xml_declaration)
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Erro na formatação XML: {e}")
            # Fallback para versão não formatada
            return f'<?xml version="{self.xml_version}" encoding="{self.encoding}"?>\n' + \
                   ET.tostring(root, encoding='unicode')
    
    def validate_xml_output(self, xml_string: str) -> Dict[str, Any]:
        """
        Valida o XML gerado contra regras básicas do SAF-T.
        
        Returns:
            Dicionário com resultado da validação
        """
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Parse XML para validação
            root = ET.fromstring(xml_string)
            
            # Validar namespace
            if not root.tag.startswith(f'{{{self.SAFT_NAMESPACE}}}'):
                validation_result['errors'].append("Namespace SAF-T incorreto")
                validation_result['is_valid'] = False
            
            # Validar estrutura básica
            required_sections = [f'{{{self.SAFT_NAMESPACE}}}Header']
            for section in required_sections:
                if root.find(f'.//{section}') is None:
                    validation_result['errors'].append(f"Seção obrigatória ausente: {section}")
                    validation_result['is_valid'] = False
            
            # Estatísticas básicas
            validation_result['stats'] = {
                'total_elements': len(root.findall('.//*')),
                'file_size': len(xml_string),
                'namespace': self.SAFT_NAMESPACE
            }
            
        except ET.ParseError as e:
            validation_result['errors'].append(f"XML malformado: {e}")
            validation_result['is_valid'] = False
            
        return validation_result


# Função utilitária para uso direto
def serialize_to_saft_xml(data: Dict[str, Any]) -> str:
    """
    Função de conveniência para serialização rápida.
    
    Args:
        data: Dados estruturados para SAF-T
        
    Returns:
        String XML SAF-T formatada
    """
    serializer = XML_Serializer()
    return serializer.serialize(data)


# Registro de namespace global para ElementTree
try:
    ET.register_namespace('', XML_Serializer.SAFT_NAMESPACE)
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
except Exception:
    # Ignorar erros de registro de namespace
    pass