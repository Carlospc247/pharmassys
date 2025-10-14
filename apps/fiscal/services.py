# apps/fiscais/services.py
import hashlib
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.core.models import Empresa
from apps.fiscal.models import AssinaturaDigital
from apps.core.services import gerar_numero_documento # Importamos a sua função de numeração

# IMPORTANTE: Use um algoritmo de hashing forte, como SHA256, conforme recomendado pela AGT.
HASH_ALGORITHM = 'sha256'

class FaturaFiscalService:
    """
    Serviço centralizado para gestão da numeração, hashing e ATCUD de documentos fiscais.
    CRÍTICO: Este serviço deve ser chamado ANTES da Fatura ser salva como 'FINALIZADA'.
    """

    def __init__(self, empresa: Empresa):
        self.empresa = empresa

    @staticmethod
    def _calcular_hash(documento_anterior_hash: str, data_emissao: str, numero_sequencial_interno: str, total_liquido: Decimal) -> str:
        """
        Calcula o Hash Criptográfico (Assinatura Digital em Cadeia).
        O hash deve incluir dados cruciais para a integridade:
        1. Hash do Documento Anterior.
        2. Data e Hora de Emissão.
        3. Número Sequencial Interno do Documento (Sem Série).
        4. Total Líquido do Documento.
        """
        # Formato de data e hora rigoroso: YYYY-MM-DDTHH:MM:SS
        data_formatada = datetime.strptime(data_emissao, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S')
        
        # A concatenação precisa ser rigorosa e documentada:
        dados_raw = f"{documento_anterior_hash}{data_formatada}{numero_sequencial_interno}{total_liquido:.2f}"
        
        # Codificar para bytes e aplicar SHA256
        hash_object = hashlib.sha256(dados_raw.encode('utf-8'))
        return hash_object.hexdigest().upper() # Retornamos em maiúsculas por convenção

        
    def assinar_e_numerar_documento(self, documento_tipo: str, total_liquido: Decimal, data_emissao: datetime) -> tuple[str, str, str]:
        """
        Função principal que aplica a lógica fiscal, acedendo aos dados da série 
        dentro do JSONField do modelo AssinaturaDigital.
        """
        with transaction.atomic():
            
            # 1. Geração do Número Sequencial e Série
            numero_documento_formatado = gerar_numero_documento(self.empresa, documento_tipo)
            
            try:
                # Exemplo de extração: pega '001' e 'FR'
                partes = numero_documento_formatado.split('/')
                numero_sequencial_puro = partes[1] 
                serie_documento_puro = numero_documento_formatado.split(' ')[0] 
            except (IndexError, AttributeError):
                 raise ValueError("Formato de número de documento inválido para extração de série/sequencial.")

            # 2. Obter o registo fiscal OneToOne da empresa
            assinatura, _ = AssinaturaDigital.objects.select_for_update().get_or_create(
                empresa=self.empresa,
                # O default aqui é um registo vazio, que deve ser preenchido
                defaults={'dados_series_fiscais': {}} 
            )
            
            # 3. Obter dados da série específica (FR, FT, etc.)
            dados_serie = assinatura.dados_series_fiscais.get(serie_documento_puro)
            
            if not dados_serie:
                # 🛑 ERRO CRÍTICO: Se a série não existir, significa que o Código AGT não foi configurado.
                raise ValueError(f"Série fiscal ({serie_documento_puro}) não configurada. Necessário inserir o Código de Validação AGT no modelo AssinaturaDigital.")

            # 4. Extrair Hash Anterior e Código AGT
            hash_anterior = dados_serie.get('ultimo_hash', '00000000000000000000000000000000') # Usa hash inicial se não houver
            
            # 🚨 FONTE DINÂMICA DO CÓDIGO AGT
            codigo_validacao_agt = dados_serie.get('codigo_agt') 
            
            if not codigo_validacao_agt:
                 raise ValueError(f"Código de Validação AGT para a série ({serie_documento_puro}) não encontrado no modelo AssinaturaDigital.")

            # 5. Calcular o Novo Hash
            hash_documento = self._calcular_hash(
                documento_anterior_hash=hash_anterior,
                data_emissao=data_emissao.strftime('%Y-%m-%d %H:%M:%S'),
                numero_sequencial_interno=numero_sequencial_puro,
                total_liquido=total_liquido
            )
            
            # 6. Atualizar o Hash na Estrutura JSON e salvar no DB
            assinatura.dados_series_fiscais[serie_documento_puro]['ultimo_hash'] = hash_documento
            assinatura.save()
            
            # 7. Geração do ATCUD
            ano = data_emissao.strftime('%y')
            atcud = f"{codigo_validacao_agt}-{serie_documento_puro}{numero_sequencial_puro}/{ano}"

            return numero_documento_formatado, hash_documento, atcud


