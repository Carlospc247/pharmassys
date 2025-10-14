# apps/integracoes/services/correios.py
from .base import BaseIntegracaoService
import requests
import xml.etree.ElementTree as ET

class CorreiosService(BaseIntegracaoService):
    """Integração com APIs dos Correios"""
    
    def consultar_postal(self, postal):
        """Consultar endereço por Postal"""
        postal_limpo = ''.join(filter(str.isdigit, postal))
        
        if len(postal_limpo) != 8:
            raise ValueError("Postal deve ter 8 dígitos")
        
        try:
            # Usar ViaCEP como alternativa mais confiável
            response = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
            data = response.json()
            
            if 'erro' in data:
                raise ValueError("Postal não encontrado")
            
            return {
                'success': True,
                'endereco': {
                    'postal': data['postal'],
                    'logradouro': data['logradouro'],
                    'bairro': data['bairro'],
                    'cidade': data['localidade'],
                    'uf': data['uf'],
                    'ibge': data['ibge']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calcular_frete(self, postal_origem, postal_destino, peso, dimensoes, valor_declarado=0):
        """Calcular frete pelos Correios"""
        
        params = {
            'nCdEmpresa': self.credenciais.get('codigo_empresa', ''),
            'sDsSenha': self.credenciais.get('senha', ''),
            'nCdServico': '04014',  # SEDEX
            'sPostalOrigemPostal_destino': postal_origem,
            'sPostalDestino': postal_destino,
            'nVlPeso': peso,
            'nCdFormato': 1,  # Caixa/Pacote
            'nVlComprimento': dimensoes.get('comprimento', 20),
            'nVlAltura': dimensoes.get('altura', 5),
            'nVlLargura': dimensoes.get('largura', 15),
            'nVlDiametro': 0,
            'sCdMaoPropria': 'N',
            'nVlValorDeclarado': valor_declarado,
            'sCdAvisoRecebimento': 'N'
        }
        
        try:
            response = self.get('calculador/CalcPrecoPrazo.aspx', params=params)
            
            # Parse XML response
            root = ET.fromstring(response.text)
            servico = root.find('.//cServico')
            
            if servico is not None:
                erro = servico.find('Erro').text
                if erro != '0':
                    raise ValueError(f"Erro Correios: {servico.find('MsgErro').text}")
                
                return {
                    'success': True,
                    'valor': float(servico.find('Valor').text.replace(',', '.')),
                    'prazo': int(servico.find('PrazoEntrega').text),
                    'servico': servico.find('Codigo').text
                }
            
            raise ValueError("Resposta inválida dos Correios")
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class WhatsAppBusinessService(BaseIntegracaoService):
    """Integração com WhatsApp Business API"""
    
    def enviar_mensagem(self, numero, mensagem, tipo='text'):
        """Enviar mensagem via WhatsApp"""
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': numero,
            'type': tipo,
            tipo: {
                'body': mensagem
            }
        }
        
        try:
            response = self.post('messages', json=payload)
            data = response.json()
            
            return {
                'success': True,
                'message_id': data.get('messages', [{}])[0].get('id'),
                'status': 'enviado'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def enviar_template(self, numero, template_name, parametros=None):
        """Enviar template pré-aprovado"""
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': numero,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {
                    'code': 'pt_BR'
                }
            }
        }
        
        if parametros:
            payload['template']['components'] = [
                {
                    'type': 'body',
                    'parameters': [
                        {'type': 'text', 'text': param} for param in parametros
                    ]
                }
            ]
        
        try:
            response = self.post('messages', json=payload)
            data = response.json()
            
            return {
                'success': True,
                'message_id': data.get('messages', [{}])[0].get('id')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class NFePaulistaService(BaseIntegracaoService):
    """Integração com NFe Paulista"""
    
    def emitir_nfe(self, dados_nfe):
        """Emitir Nota Fiscal Eletrônica"""
        
        payload = {
            'tipo_documento': 'NFe',
            'natureza_operacao': dados_nfe.get('natureza_operacao', 'Venda'),
            'emitente': {
                'nif': self.empresa.nif,
                'nome': self.empresa.nome,
                'endereco': self._formatar_endereco_empresa()
            },
            'destinatario': dados_nfe['destinatario'],
            'itens': dados_nfe['itens'],
            'valores': dados_nfe['valores'],
            'formas_pagamento': dados_nfe.get('formas_pagamento', [])
        }
        
        try:
            response = self.post('nfe', json=payload)
            data = response.json()
            
            return {
                'success': True,
                'numero_nfe': data.get('numero'),
                'chave_acesso': data.get('chave_acesso'),
                'status': data.get('status'),
                'xml': data.get('xml'),
                'pdf': data.get('pdf')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def consultar_status_nfe(self, chave_acesso):
        """Consultar status da NFe"""
        
        try:
            response = self.get(f'nfe/{chave_acesso}/status')
            data = response.json()
            
            return {
                'success': True,
                'status': data.get('status'),
                'motivo': data.get('motivo'),
                'data_autorizacao': data.get('data_autorizacao')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _formatar_endereco_empresa(self):
        """Formatar endereço da empresa para NFe"""
        return {
            'logradouro': self.empresa.endereco,
            'numero': self.empresa.numero,
            'bairro': self.empresa.bairro,
            'cep': self.empresa.cep,
            'municipio': self.empresa.cidade,
            'uf': self.empresa.estado
        }

class PagSeguroService(BaseIntegracaoService):
    """Integração com PagSeguro"""
    
    def criar_cobranca(self, dados_cobranca):
        """Criar cobrança no PagSeguro"""
        
        payload = {
            'reference_id': dados_cobranca['referencia'],
            'description': dados_cobranca['descricao'],
            'amount': {
                'value': int(dados_cobranca['valor'] * 100),  # Valor em centavos
                'currency': 'BRL'
            },
            'payment_methods': dados_cobranca.get('metodos_pagamento', [
                {'type': 'CREDIT_CARD'},
                {'type': 'DEBIT_CARD'},
                {'type': 'KWIK'}
            ]),
            'customer': dados_cobranca['cliente'],
            'notification_urls': [
                f"{settings.SITE_URL}/webhooks/pagseguro/"
            ]
        }
        
        try:
            response = self.post('orders', json=payload)
            data = response.json()
            
            return {
                'success': True,
                'order_id': data.get('id'),
                'links': data.get('links', []),
                'status': data.get('status')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def consultar_transacao(self, transaction_id):
        """Consultar status da transação"""
        
        try:
            response = self.get(f'orders/{transaction_id}')
            data = response.json()
            
            return {
                'success': True,
                'status': data.get('status'),
                'amount': data.get('amount', {}).get('value', 0) / 100,
                'payment_method': data.get('charges', [{}])[0].get('payment_method', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class ContabilidadeOnlineService(BaseIntegracaoService):
    """Integração com sistemas de contabilidade online"""
    
    def enviar_movimento_financeiro(self, movimento):
        """Enviar movimento financeiro para contabilidade"""
        
        payload = {
            'data': movimento['data'].isoformat(),
            'tipo': movimento['tipo'],  # 'receita' ou 'despesa'
            'valor': float(movimento['valor']),
            'descricao': movimento['descricao'],
            'categoria': movimento.get('categoria'),
            'centro_custo': movimento.get('centro_custo'),
            'documento': movimento.get('numero_documento'),
            'observacoes': movimento.get('observacoes')
        }
        
        try:
            response = self.post('movimentos', json=payload)
            data = response.json()
            
            return {
                'success': True,
                'id_movimento': data.get('id'),
                'status': 'enviado'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def obter_plano_contas(self):
        """Obter plano de contas"""
        
        try:
            response = self.get('plano-contas')
            data = response.json()
            
            return {
                'success': True,
                'contas': data.get('contas', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

