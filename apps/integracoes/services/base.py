# apps/integracoes/services/base.py
import requests
import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from ..models import LogIntegracao, ConfiguracaoIntegracao

logger = logging.getLogger(__name__)

class BaseIntegracaoService:
    """Classe base para serviços de integração"""
    
    def __init__(self, configuracao: ConfiguracaoIntegracao):
        self.configuracao = configuracao
        self.empresa = configuracao.empresa
        self.tipo = configuracao.tipo_integracao
        self.credenciais = configuracao.get_credenciais()
        
        # Configurar session
        self.session = requests.Session()
        self.setup_authentication()
    
    def setup_authentication(self):
        """Configurar autenticação na sessão"""
        if self.tipo.metodo_autenticacao == 'api_key':
            if 'api_key' in self.credenciais:
                self.session.headers.update({
                    'X-API-Key': self.credenciais['api_key']
                })
        
        elif self.tipo.metodo_autenticacao == 'bearer_token':
            if 'token' in self.credenciais:
                self.session.headers.update({
                    'Authorization': f"Bearer {self.credenciais['token']}"
                })
        
        elif self.tipo.metodo_autenticacao == 'basic_auth':
            if 'username' in self.credenciais and 'password' in self.credenciais:
                self.session.auth = (
                    self.credenciais['username'],
                    self.credenciais['password']
                )
    
    def can_make_request(self):
        """Verificar se pode fazer requisição (limite de rate)"""
        hoje = timezone.now().date()
        
        if self.configuracao.ultima_utilizacao:
            if self.configuracao.ultima_utilizacao.date() != hoje:
                # Reset contador diário
                self.configuracao.requests_utilizadas_hoje = 0
                self.configuracao.save()
        
        return self.configuracao.requests_utilizadas_hoje < self.configuracao.limite_requests_dia
    
    def make_request(self, method, endpoint, **kwargs):
        """Fazer requisição HTTP com logs e controle de rate"""
        
        if not self.can_make_request():
            raise Exception("Limite diário de requisições excedido")
        
        url = f"{self.tipo.url_base.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Preparar dados do log
        log_data = {
            'configuracao': self.configuracao,
            'tipo': 'request',
            'metodo': method.upper(),
            'url': url,
            'headers': dict(self.session.headers),
            'payload': str(kwargs.get('json', kwargs.get('data', ''))),
            'contexto': kwargs.pop('contexto', {}),
            'usuario': kwargs.pop('usuario', None)
        }
        
        start_time = time.time()
        
        try:
            # Fazer requisição
            response = self.session.request(method, url, **kwargs)
            
            # Calcular tempo de resposta
            tempo_resposta = time.time() - start_time
            
            # Atualizar contadores
            self.configuracao.requests_utilizadas_hoje += 1
            self.configuracao.ultima_utilizacao = timezone.now()
            self.configuracao.save()
            
            # Log da resposta
            log_data.update({
                'status': 'sucesso' if response.ok else 'erro',
                'status_code': response.status_code,
                'response_data': response.text,
                'tempo_resposta': tempo_resposta
            })
            
            LogIntegracao.objects.create(**log_data)
            
            # Verificar se resposta é válida
            if not response.ok:
                response.raise_for_status()
            
            return response
            
        except requests.exceptions.Timeout:
            log_data.update({
                'status': 'timeout',
                'tempo_resposta': time.time() - start_time
            })
            LogIntegracao.objects.create(**log_data)
            raise
            
        except requests.exceptions.RequestException as e:
            log_data.update({
                'status': 'erro',
                'response_data': str(e),
                'tempo_resposta': time.time() - start_time
            })
            LogIntegracao.objects.create(**log_data)
            raise
    
    def get(self, endpoint, **kwargs):
        """GET request"""
        return self.make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        """POST request"""
        return self.make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint, **kwargs):
        """PUT request"""
        return self.make_request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        """DELETE request"""
        return self.make_request('DELETE', endpoint, **kwargs)
    
    def test_connection(self):
        """Testar conexão com a API"""
        try:
            response = self.get('/')
            return {
                'success': True,
                'status_code': response.status_code,
                'message': 'Conexão estabelecida com sucesso'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Falha ao conectar com a API'
            }