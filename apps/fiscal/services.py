import logging
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64

from .models import TaxaIVAAGT, AssinaturaDigital, RetencaoFonte
from apps.core.models import Empresa
from apps.financeiro.models import LancamentoFinanceiro, PlanoContas
from apps.vendas.models import Venda

# Configuração de logging
logger = logging.getLogger('fiscais')

class FiscalServiceError(Exception):
    """Exceção personalizada para erros nos serviços fiscais"""
    pass

class TaxaIVAService:
    """
    Serviço para gestão de Taxas de IVA compatível com SAF-T AO v1.01
    """
    
    @staticmethod
    def criar_taxa_iva(empresa: Empresa, dados: Dict) -> TaxaIVAAGT:
        """
        Cria uma nova taxa de IVA com validações SAF-T
        
        Args:
            empresa: Empresa proprietária da taxa
            dados: Dicionário com dados da taxa
            
        Returns:
            TaxaIVAAGT: Taxa criada
            
        Raises:
            FiscalServiceError: Se houver erro na criação
        """
        try:
            with transaction.atomic():
                # Validações SAF-T específicas
                TaxaIVAService._validar_dados_saft(dados)
                
                taxa = TaxaIVAAGT.objects.create(
                    empresa=empresa,
                    nome=dados['nome'],
                    tax_type=dados['tax_type'],
                    tax_code=dados['tax_code'],
                    tax_percentage=dados.get('tax_percentage', Decimal('0.00')),
                    exemption_reason=dados.get('exemption_reason'),
                    legislacao_referencia=dados.get('legislacao_referencia', ''),
                    ativo=dados.get('ativo', True)
                )
                
                logger.info(
                    f"Taxa IVA criada: {taxa.nome} para empresa {empresa.nome}",
                    extra={
                        'empresa_id': empresa.id,
                        'taxa_id': taxa.id,
                        'tax_type': taxa.tax_type,
                        'tax_percentage': float(taxa.tax_percentage)
                    }
                )
                
                return taxa
                
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar taxa IVA: {e}")
            raise FiscalServiceError(f"Dados inválidos: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao criar taxa IVA: {e}")
            raise FiscalServiceError(f"Erro interno: {e}")
    
    @staticmethod
    def _validar_dados_saft(dados: Dict) -> None:
        """Valida dados conforme especificação SAF-T AO"""
        
        # Validar tax_type
        if dados['tax_type'] not in ['IVA', 'IS', 'NS']:
            raise ValidationError("tax_type deve ser IVA, IS ou NS")
        
        # Se for IVA, deve ter tax_percentage
        if dados['tax_type'] == 'IVA':
            if not dados.get('tax_percentage') or dados['tax_percentage'] < 0:
                raise ValidationError("IVA deve ter tax_percentage válida")
        
        # Se for IS ou NS, deve ter exemption_reason
        if dados['tax_type'] in ['IS', 'NS']:
            if not dados.get('exemption_reason'):
                raise ValidationError("Isenções e não sujeições devem ter exemption_reason")
    
    @staticmethod
    def obter_taxas_ativas(empresa: Empresa) -> List[TaxaIVAAGT]:
        """Obtém todas as taxas ativas de uma empresa"""
        return TaxaIVAAGT.objects.filter(
            empresa=empresa,
            ativo=True
        ).order_by('tax_type', '-tax_percentage')
    
    @staticmethod
    def calcular_iva(valor_base: Decimal, taxa: TaxaIVAAGT) -> Dict[str, Decimal]:
        """
        Calcula o IVA baseado no valor base e taxa
        
        Returns:
            Dict com valor_base, valor_iva, valor_total
        """
        if taxa.tax_type != 'IVA':
            return {
                'valor_base': valor_base,
                'valor_iva': Decimal('0.00'),
                'valor_total': valor_base,
                'taxa_aplicada': Decimal('0.00'),
                'motivo_isencao': taxa.exemption_reason
            }
        
        valor_iva = valor_base * (taxa.tax_percentage / Decimal('100.00'))
        valor_total = valor_base + valor_iva
        
        return {
            'valor_base': valor_base,
            'valor_iva': valor_iva,
            'valor_total': valor_total,
            'taxa_aplicada': taxa.tax_percentage
        }

class AssinaturaDigitalService:
    """
    Serviço para gestão de assinatura digital e hash de documentos SAF-T
    """
    
    @staticmethod
    def gerar_chaves_rsa(empresa: Empresa, tamanho_chave: int = 2048) -> AssinaturaDigital:
        """
        Gera um par de chaves RSA para a empresa
        
        Args:
            empresa: Empresa proprietária das chaves
            tamanho_chave: Tamanho da chave RSA em bits
            
        Returns:
            AssinaturaDigital: Objeto com chaves geradas
        """
        try:
            # Gerar chave privada
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=tamanho_chave,
                backend=default_backend()
            )
            
            # Serializar chave privada
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Obter chave pública
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Criar ou atualizar assinatura digital
            assinatura, created = AssinaturaDigital.objects.get_or_create(
                empresa=empresa,
                defaults={
                    'chave_privada': private_pem.decode('utf-8'),
                    'chave_publica': public_pem.decode('utf-8'),
                    'dados_series_fiscais': {}
                }
            )
            
            if not created:
                assinatura.chave_privada = private_pem.decode('utf-8')
                assinatura.chave_publica = public_pem.decode('utf-8')
                assinatura.save()
            
            logger.info(
                f"Chaves RSA geradas para empresa {empresa.nome}",
                extra={
                    'empresa_id': empresa.id,
                    'tamanho_chave': tamanho_chave,
                    'created': created
                }
            )
            
            return assinatura
            
        except Exception as e:
            logger.error(f"Erro ao gerar chaves RSA: {e}")
            raise FiscalServiceError(f"Erro na geração de chaves: {e}")
    
    @staticmethod
    def calcular_hash_documento(dados_documento: Dict, hash_anterior: str = "") -> str:
        """
        Calcula o hash de um documento para cadeia de integridade SAF-T
        
        Args:
            dados_documento: Dados do documento a ser assinado
            hash_anterior: Hash do documento anterior na cadeia
            
        Returns:
            str: Hash SHA-256 em base64
        """
        try:
            # Preparar dados para hash conforme SAF-T AO
            dados_ordenados = {
                'data': dados_documento.get('data', ''),
                'tipo_documento': dados_documento.get('tipo_documento', ''),
                'serie': dados_documento.get('serie', ''),
                'numero': dados_documento.get('numero', ''),
                'valor_total': str(dados_documento.get('valor_total', '0.00')),
                'hash_anterior': hash_anterior
            }
            
            # Criar string ordenada para hash
            string_hash = ';'.join([
                f"{k}:{v}" for k, v in sorted(dados_ordenados.items())
            ])
            
            # Calcular hash SHA-256
            hash_obj = hashlib.sha256(string_hash.encode('utf-8'))
            hash_base64 = base64.b64encode(hash_obj.digest()).decode('utf-8')
            
            logger.debug(
                f"Hash calculado para documento",
                extra={
                    'tipo_documento': dados_documento.get('tipo_documento'),
                    'numero': dados_documento.get('numero'),
                    'hash_length': len(hash_base64)
                }
            )
            
            return hash_base64
            
        except Exception as e:
            logger.error(f"Erro ao calcular hash: {e}")
            raise FiscalServiceError(f"Erro no cálculo de hash: {e}")
    
    @staticmethod
    def assinar_documento(empresa: Empresa, dados_documento: Dict) -> Dict[str, str]:
        """
        Assina um documento digitalmente e atualiza a cadeia de hash
        
        Args:
            empresa: Empresa proprietária do documento
            dados_documento: Dados do documento
            
        Returns:
            Dict com hash e assinatura do documento
        """
        try:
            with transaction.atomic():
                assinatura_digital = AssinaturaDigital.objects.get(empresa=empresa)
                
                # Obter último hash da série
                serie = dados_documento.get('serie', 'DEFAULT')
                ultimo_hash = assinatura_digital.dados_series_fiscais.get(
                    serie, {}).get('ultimo_hash', '')
                
                # Calcular novo hash
                novo_hash = AssinaturaDigitalService.calcular_hash_documento(
                    dados_documento, ultimo_hash
                )
                
                # Assinar o hash
                private_key = serialization.load_pem_private_key(
                    assinatura_digital.chave_privada.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                
                signature = private_key.sign(
                    novo_hash.encode('utf-8'),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                assinatura_base64 = base64.b64encode(signature).decode('utf-8')
                
                # Atualizar série fiscal
                if serie not in assinatura_digital.dados_series_fiscais:
                    assinatura_digital.dados_series_fiscais[serie] = {}
                
                assinatura_digital.dados_series_fiscais[serie].update({
                    'ultimo_hash': novo_hash,
                    'ultimo_documento': dados_documento.get('numero'),
                    'data_ultima_assinatura': timezone.now().isoformat()
                })
                
                assinatura_digital.ultimo_hash = novo_hash
                assinatura_digital.save()
                
                logger.info(
                    f"Documento assinado digitalmente",
                    extra={
                        'empresa_id': empresa.id,
                        'serie': serie,
                        'numero': dados_documento.get('numero'),
                        'tipo_documento': dados_documento.get('tipo_documento')
                    }
                )
                
                return {
                    'hash': novo_hash,
                    'assinatura': assinatura_base64,
                    'hash_anterior': ultimo_hash
                }
                
        except AssinaturaDigital.DoesNotExist:
            logger.error(f"Assinatura digital não encontrada para empresa {empresa.id}")
            raise FiscalServiceError("Assinatura digital não configurada")
        except Exception as e:
            logger.error(f"Erro ao assinar documento: {e}")
            raise FiscalServiceError(f"Erro na assinatura: {e}")

class RetencaoFonteService:
    """
    Serviço para gestão de retenções na fonte
    """
    
    @staticmethod
    def criar_retencao(dados: Dict) -> RetencaoFonte:
        """
        Cria uma nova retenção na fonte com lançamentos contábeis
        
        Args:
            dados: Dados da retenção
            
        Returns:
            RetencaoFonte: Retenção criada
        """
        try:
            with transaction.atomic():
                retencao = RetencaoFonte.objects.create(**dados)
                
                # Gerar lançamento contábil
                RetencaoFonteService._gerar_lancamento_contabil(retencao)
                
                logger.info(
                    f"Retenção na fonte criada",
                    extra={
                        'retencao_id': retencao.id,
                        'tipo_retencao': retencao.tipo_retencao,
                        'valor_retido': float(retencao.valor_retido),
                        'fornecedor_id': retencao.fornecedor.id
                    }
                )
                
                return retencao
                
        except Exception as e:
            logger.error(f"Erro ao criar retenção: {e}")
            raise FiscalServiceError(f"Erro na criação: {e}")
    
    @staticmethod
    def _gerar_lancamento_contabil(retencao: RetencaoFonte) -> None:
        """Gera lançamentos contábeis para a retenção"""
        try:
            # Buscar planos de contas
            conta_impostos_pagar = PlanoContas.objects.filter(
                empresa=retencao.empresa,
                tipo_conta='passivo',
                nome__icontains='impostos'
            ).first()
            
            if not conta_impostos_pagar:
                logger.warning("Plano de contas 'Impostos a Pagar' não encontrado")
                return
            
            # Criar lançamento de débito (Impostos a Pagar)
            LancamentoFinanceiro.objects.create(
                numero_lancamento=f"RET{retencao.id:06d}D",
                data_lancamento=retencao.data_retencao,
                descricao=f"Retenção {retencao.tipo_retencao} - {retencao.referencia_documento}",
                tipo='debito',
                valor=retencao.valor_retido,
                plano_contas=conta_impostos_pagar,
                usuario_responsavel=retencao.conta_pagar.empresa.funcionarios.first().usuario,
                empresa=retencao.empresa
            )
            
            logger.debug(
                f"Lançamento contábil gerado para retenção {retencao.id}",
                extra={'valor': float(retencao.valor_retido)}
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar lançamento contábil: {e}")
    
    @staticmethod
    def processar_pagamento_estado(retencao_id: int, data_pagamento: date) -> RetencaoFonte:
        """
        Marca uma retenção como paga ao Estado
        
        Args:
            retencao_id: ID da retenção
            data_pagamento: Data do pagamento
            
        Returns:
            RetencaoFonte: Retenção atualizada
        """
        try:
            with transaction.atomic():
                retencao = RetencaoFonte.objects.get(id=retencao_id)
                retencao.paga_ao_estado = True
                retencao.save()
                
                logger.info(
                    f"Retenção marcada como paga ao Estado",
                    extra={
                        'retencao_id': retencao_id,
                        'data_pagamento': data_pagamento.isoformat(),
                        'valor': float(retencao.valor_retido)
                    }
                )
                
                return retencao
                
        except RetencaoFonte.DoesNotExist:
            logger.error(f"Retenção {retencao_id} não encontrada")
            raise FiscalServiceError("Retenção não encontrada")
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
            raise FiscalServiceError(f"Erro no processamento: {e}")

class SAFTExportService:
    """
    Serviço para exportação de dados no formato SAF-T AO v1.01
    """
    
    @staticmethod
    def gerar_saft_ao(empresa: Empresa, data_inicio: date, data_fim: date) -> str:
        """
        Gera arquivo SAF-T AO completo para o período especificado
        
        Args:
            empresa: Empresa a exportar
            data_inicio: Data de início do período
            data_fim: Data de fim do período
            
        Returns:
            str: XML SAF-T AO v1.01
        """
        try:
            logger.info(
                f"Iniciando geração SAF-T AO",
                extra={
                    'empresa_id': empresa.id,
                    'data_inicio': data_inicio.isoformat(),
                    'data_fim': data_fim.isoformat()
                }
            )
            
            # Criar estrutura XML base
            root = ET.Element("AuditFile", xmlns="urn:OECD:StandardAuditFile-Tax:AO_1.01_01")
            
            # Header
            header = SAFTExportService._criar_header(empresa, data_inicio, data_fim)
            root.append(header)
            
            # Master Files
            master_files = SAFTExportService._criar_master_files(empresa)
            root.append(master_files)
            
            # Source Documents
            source_documents = SAFTExportService._criar_source_documents(
                empresa, data_inicio, data_fim
            )
            root.append(source_documents)
            
            # Converter para string XML
            xml_string = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            xml_formatted = xml_string.decode('utf-8')
            
            logger.info(
                f"SAF-T AO gerado com sucesso",
                extra={
                    'empresa_id': empresa.id,
                    'xml_size': len(xml_formatted)
                }
            )
            
            return xml_formatted
            
        except Exception as e:
            logger.error(f"Erro ao gerar SAF-T AO: {e}")
            raise FiscalServiceError(f"Erro na geração: {e}")
    
    @staticmethod
    def _criar_header(empresa: Empresa, data_inicio: date, data_fim: date) -> ET.Element:
        """Cria o bloco Header do SAF-T"""
        header = ET.Element("Header")
        
        # Audit File Version
        ET.SubElement(header, "AuditFileVersion").text = "1.01_01"
        
        # Company ID
        ET.SubElement(header, "CompanyID").text = empresa.nif or empresa.id
        
        # Tax Registration Number
        ET.SubElement(header, "TaxRegistrationNumber").text = empresa.nif
        
        # Tax Accounting Basis
        ET.SubElement(header, "TaxAccountingBasis").text = "F"  # Faturação
        
        # Company Name
        ET.SubElement(header, "CompanyName").text = empresa.nome
        
        # Business Name (se diferente)
        ET.SubElement(header, "BusinessName").text = empresa.nome_comercial or empresa.nome
        
        # Company Address
        address = ET.SubElement(header, "CompanyAddress")
        ET.SubElement(address, "AddressDetail").text = empresa.endereco_completo or ""
        ET.SubElement(address, "City").text = empresa.cidade or ""
        ET.SubElement(address, "PostalCode").text = empresa.codigo_postal or ""
        ET.SubElement(address, "Country").text = "AO"
        
        # Fiscal Year
        ET.SubElement(header, "FiscalYear").text = str(data_inicio.year)
        
        # Start Date
        ET.SubElement(header, "StartDate").text = data_inicio.strftime("%Y-%m-%d")
        
        # End Date
        ET.SubElement(header, "EndDate").text = data_fim.strftime("%Y-%m-%d")
        
        # Currency Code
        ET.SubElement(header, "CurrencyCode").text = "AOA"
        
        # Date Created
        ET.SubElement(header, "DateCreated").text = timezone.now().strftime("%Y-%m-%d")
        
        # Time Created
        ET.SubElement(header, "TimeCreated").text = timezone.now().strftime("%H:%M:%S")
        
        # Product ID
        ET.SubElement(header, "ProductID").text = "PharmaSys Fiscal"
        
        # Product Version
        ET.SubElement(header, "ProductVersion").text = "1.0"
        
        return header
    
    @staticmethod
    def _criar_master_files(empresa: Empresa) -> ET.Element:
        """Cria o bloco MasterFiles do SAF-T"""
        master_files = ET.Element("MasterFiles")
        
        # General Ledger Accounts
        gl_accounts = ET.SubElement(master_files, "GeneralLedgerAccounts")
        
        for conta in empresa.planos_contas.filter(ativo=True):
            account = ET.SubElement(gl_accounts, "Account")
            ET.SubElement(account, "AccountID").text = conta.codigo
            ET.SubElement(account, "AccountDescription").text = conta.nome
            ET.SubElement(account, "StandardAccountID").text = conta.codigo
            ET.SubElement(account, "AccountType").text = conta.tipo_conta.upper()
        
        # Tax Table
        tax_table = ET.SubElement(master_files, "TaxTable")
        
        for taxa in empresa.taxas_iva.filter(ativo=True):
            tax_entry = ET.SubElement(tax_table, "TaxTableEntry")
            ET.SubElement(tax_entry, "TaxType").text = taxa.tax_type
            ET.SubElement(tax_entry, "TaxCode").text = taxa.tax_code
            ET.SubElement(tax_entry, "Description").text = taxa.nome
            
            if taxa.tax_type == 'IVA':
                ET.SubElement(tax_entry, "TaxPercentage").text = str(taxa.tax_percentage)
            else:
                ET.SubElement(tax_entry, "TaxExemptionCode").text = taxa.exemption_reason
        
        return master_files
    
    @staticmethod
    def _criar_source_documents(empresa: Empresa, data_inicio: date, data_fim: date) -> ET.Element:
        """Cria o bloco SourceDocuments do SAF-T"""
        source_documents = ET.Element("SourceDocuments")
        
        # Sales Invoices
        sales_invoices = ET.SubElement(source_documents, "SalesInvoices")
        ET.SubElement(sales_invoices, "NumberOfEntries").text = "0"
        ET.SubElement(sales_invoices, "TotalDebit").text = "0.00"
        ET.SubElement(sales_invoices, "TotalCredit").text = "0.00"
        
        # Adicionar vendas se existirem
        vendas = Venda.objects.filter(
            empresa=empresa,
            data_venda__range=[data_inicio, data_fim]
        )
        
        ET.SubElement(sales_invoices, "NumberOfEntries").text = str(vendas.count())
        
        # Working Documents (se houver)
        working_documents = ET.SubElement(source_documents, "WorkingDocuments")
        ET.SubElement(working_documents, "NumberOfEntries").text = "0"
        ET.SubElement(working_documents, "TotalDebit").text = "0.00"
        ET.SubElement(working_documents, "TotalCredit").text = "0.00"
        
        # Payments (se houver)
        payments = ET.SubElement(source_documents, "Payments")
        ET.SubElement(payments, "NumberOfEntries").text = "0"
        ET.SubElement(payments, "TotalDebit").text = "0.00"
        ET.SubElement(payments, "TotalCredit").text = "0.00"
        
        return source_documents

class FiscalDashboardService:
    """
    Serviço para métricas e dashboard fiscal
    """
    
    @staticmethod
    def obter_metricas_fiscais(empresa: Empresa, periodo: Tuple[date, date]) -> Dict:
        """
        Obtém métricas fiscais para dashboard
        
        Args:
            empresa: Empresa
            periodo: Tupla com data início e fim
            
        Returns:
            Dict com métricas fiscais
        """
        data_inicio, data_fim = periodo
        
        try:
            # Retenções no período
            retencoes = RetencaoFonte.objects.filter(
                empresa=empresa,
                data_retencao__range=[data_inicio, data_fim]
            )
            
            total_retencoes = sum(r.valor_retido for r in retencoes)
            retencoes_pagas = retencoes.filter(paga_ao_estado=True).count()
            retencoes_pendentes = retencoes.filter(paga_ao_estado=False).count()
            
            # Taxas ativas
            taxas_ativas = TaxaIVAAGT.objects.filter(empresa=empresa, ativo=True).count()
            
            # Documentos assinados
            assinatura = AssinaturaDigital.objects.filter(empresa=empresa).first()
            series_ativas = len(assinatura.dados_series_fiscais) if assinatura else 0
            
            metricas = {
                'retencoes': {
                    'total_valor': float(total_retencoes),
                    'total_count': retencoes.count(),
                    'pagas_count': retencoes_pagas,
                    'pendentes_count': retencoes_pendentes
                },
                'taxas': {
                    'ativas_count': taxas_ativas
                },
                'assinatura': {
                    'configurada': assinatura is not None,
                    'series_ativas': series_ativas,
                    'ultimo_hash': assinatura.ultimo_hash[:20] + '...' if assinatura and assinatura.ultimo_hash else None
                }
            }
            
            logger.info(
                f"Métricas fiscais calculadas",
                extra={
                    'empresa_id': empresa.id,
                    'periodo': f"{data_inicio} - {data_fim}",
                    'total_retencoes': float(total_retencoes)
                }
            )
            
            return metricas
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas fiscais: {e}")
            raise FiscalServiceError(f"Erro no cálculo: {e}")

