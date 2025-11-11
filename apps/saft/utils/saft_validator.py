# apps/saft/utils/saft_validator.py

import os
from lxml import etree
from typing import Optional, List

# 🚨 Configuração de Produção: 
# Ajuste o caminho para o XSD conforme a versão mais recente da AGT.
SAFT_XSD_PATH = os.path.join(os.path.dirname(__file__), '..', 'SAFT_AO_1.04_01.xsd')

class SaftValidator:
    """
    Serviço de Validação do XML SAF-T contra o XSD oficial.
    Crucial para garantir a aceitação do ficheiro pela AGT.
    """
    
    def __init__(self):
        if not os.path.exists(SAFT_XSD_PATH):
            raise FileNotFoundError(
                f"ERRO: Ficheiro XSD não encontrado em {SAFT_XSD_PATH}. "
                "Obtenha o schema oficial da AGT e coloque-o neste caminho."
            )
        self.xmlschema: etree.XMLSchema = self._load_xsd()

    def _load_xsd(self) -> etree.XMLSchema:
        """ Carrega o schema XSD (Definition) para uso futuro. """
        print(f"Carregando XSD de: {SAFT_XSD_PATH}...")
        with open(SAFT_XSD_PATH, 'rb') as f:
            xmlschema_doc = etree.parse(f)
        return etree.XMLSchema(xmlschema_doc)

    def validate_xml_string(self, xml_content: str) -> Optional[List[str]]:
        """
        Valida o conteúdo de uma string XML contra o schema carregado.
        Retorna uma lista de erros (se houver) ou None (se válido).
        """
        try:
            # 1. Parsear a string XML gerada
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # 2. Executar a validação
            self.xmlschema.assertValid(xml_doc)
            
            # 3. Sucesso na validação
            print("✅ VALIDAÇÃO BEM-SUCEDIDA: O ficheiro SAF-T está em conformidade com o XSD.")
            return None 

        except etree.XMLSyntaxError as e:
            # Erros de sintaxe XML básico
            print(f"❌ ERRO DE SINTAXE XML: {e}")
            return [str(e)]

        except etree.DocumentInvalid as e:
            # Erros de schema (falha ao aderir ao XSD)
            print("❌ ERRO DE CONFORMIDADE XSD: O ficheiro falhou na validação do schema.")
            errors = [log.message for log in self.xmlschema.error_log]
            return errors
        
        except Exception as e:
            # Outros erros
            print(f"❌ ERRO INESPERADO: {e}")
            return [str(e)]

