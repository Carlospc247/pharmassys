# apps/saft/views.py


from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from datetime import datetime, date
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.fiscal.models import TaxaIVAAGT
from apps.saft.models import SaftXmlGeneratorService
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages

# 🚨 Assumindo a importação dos seus serviços e modelos
# from .services import SaftXmlGeneratorService 
# from apps.core.models import Empresa 
# from apps.fiscais.models import TaxaIVAAGT # Necessário para o TaxTable


class SaftExportView(LoginRequiredMixin, View, AccessMixin):
    """
    View para solicitar e servir o ficheiro SAF-T (AO) XML.
    Garante que apenas utilizadores logados podem aceder.
    """ 

    template_name = 'saft/saft_export_form.html'

    def test_func(self):
        """ Verifica se o utilizador tem a permissão 'saft.export_saft'. """
        # O UserPassesTestMixin irá redirecionar o utilizador sem permissão para 403 (Forbidden)
        return self.request.user.has_perm('saft.export_saft')
    
    def test_func(self):
        """ Verifica se o utilizador tem a permissão 'saft.export_saft'. """
        # O UserPassesTestMixin irá redirecionar o utilizador sem permissão para 403 (Forbidden)
        return self.request.user.has_perm('saft.export_saft')
    
    def get(self, request):
        """ Renderiza o formulário de seleção de datas. """
        # Poderia pré-preencher com o mês anterior
        return render(request, self.template_name)

    def post(self, request):
        """ Processa o formulário e gera o ficheiro XML. """
        
        # 1. Validação de Acesso (RBAC Implícito)
        # 🚨 AQUI DEVE ENTRAR A VALIDAÇÃO DE PERMISSÃO (Ex: é gestor fiscal?)
        if not request.user.has_perm('saft.export_saft'):
            return HttpResponse("Acesso negado. Requer permissão de Gestor Fiscal.", status=403)

        # 2. Captura e Conversão das Datas
        try:
            # As datas vêm como strings do formulário HTML
            data_inicio_str = request.POST.get('data_inicio')
            data_fim_str = request.POST.get('data_fim')
            
            # Conversão para objetos datetime.date para precisão fiscal
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            
            # Ajustar para o fuso horário (necessário para consultas DateTimeField)
            data_inicio_dt = datetime.combine(data_inicio, datetime.min.time(), tzinfo=request.user.empresa.timezone) 
            data_fim_dt = datetime.combine(data_fim, datetime.max.time(), tzinfo=request.user.empresa.timezone)
            

        except (ValueError, TypeError):
            # Retorna um erro amigável se o formato da data estiver incorreto
            return render(request, self.template_name, {'error': 'Formato de data inválido. Use AAAA-MM-DD.'})
        
        # 3. Execução do Serviço de Geração de XML
        
        # A empresa logada é extraída do utilizador (Assumindo request.user.empresa existe)
        empresa_ativa = request.user.empresa 
        
        try:
            generator = SaftXmlGeneratorService(
                empresa=empresa_ativa,
                data_inicio=data_inicio_dt,
                data_fim=data_fim_dt
            )
            
            
            # A geração exige a Tabela de Impostos (TaxaIVAAGT)
            xml_content = generator.generate_xml(TaxaIVAAGT) 
            # 🚨 LOGGING CRÍTICO
            print(f"SAF-T EXPORTADO: Utilizador '{request.user.username}' exportou dados de {data_inicio_str} a {data_fim_str} para a Empresa '{empresa_ativa.nome}'.")

            

        except Exception as e:
            # Logar o erro (CRÍTICO em produção)
            print(f"ERRO CRÍTICO NA GERAÇÃO SAF-T: {e}") 
            return render(request, self.template_name, {'error': f'Falha ao gerar o SAF-T: {e}'})
        
        # 4. Resposta de Download (HTTP Response)
        
        # Nome do Ficheiro (Padrão SAF-T: NIF_DATAINICIO_DATAFIM.xml)
        filename = f"{empresa_ativa.nif}_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.xml"
        
        response = HttpResponse(xml_content, content_type='application/xml')
        
        # Este cabeçalho força o browser a descarregar o ficheiro em vez de o exibir
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

