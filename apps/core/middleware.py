# apps/core/middleware.py
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

class AccountsProfileRedirectMiddleware:
    """
    Middleware para interceptar e redirecionar /accounts/profile/ 
    ANTES que chegue ao sistema de URLs
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Interceptar /accounts/profile/ e redirecionar imediatamente
        if request.path == '/accounts/profile/':
            if request.user.is_authenticated:
                return HttpResponseRedirect('/')
            else:
                return HttpResponseRedirect('/accounts/login/')
        
        # Interceptar outras variações possíveis
        if request.path.startswith('/accounts/profile'):
            return HttpResponseRedirect('/')
        
        response = self.get_response(request)
        return response

# apps/core/middleware.py - Middleware para logging

import logging
from django.utils.deprecation import MiddlewareMixin

class DocumentLogMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 'documentos/gerar' in request.path and response.status_code == 200:
            logger = logging.getLogger('documentos')
            logger.info(f'Documento gerado: {request.path} - Usuário: {request.user.username if request.user.is_authenticated else "Anônimo"}')
        return response

