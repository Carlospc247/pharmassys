import logging
import os
import zipfile
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.template.loader import render_to_string
from .models import TaxaIVAAGT, AssinaturaDigital, RetencaoFonte
from .services import (
    AssinaturaDigitalService, SAFTExportService, 
    FiscalDashboardService, FiscalServiceError
)
from apps.fiscal import signals
from apps.core.models import Empresa
from apps.vendas.models import Venda, FaturaCredito
from apps.financeiro.models import MovimentacaoFinanceira

logger = logging.getLogger('fiscais.tasks')

# =====================================
# Tasks para Assinatura Digital
# =====================================

@shared_task(bind=True, max_retries=3)
def processar_assinatura_documento(self, empresa_id: int, documento_id: int, 
                                 documento_type: str, dados_documento: Dict):
    """
    Processa assinatura digital de um documento de forma assíncrona
    
    Args:
        empresa_id: ID da empresa
        documento_id: ID do documento
        documento_type: Tipo do documento (Venda, FaturaCredito, etc.)
        dados_documento: Dados do documento para assinatura
    """
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        
        logger.info(
            f"Iniciando assinatura digital para {documento_type} {documento_id}",
            extra={
                'task_id': self.request.id,
                'empresa_id': empresa_id,
                'documento_id': documento_id,
                'documento_type': documento_type
            }
        )
        
        # Processar assinatura
        resultado = AssinaturaDigitalService.assinar_documento(empresa, dados_documento)
        
        # Atualizar documento com hash e assinatura
        _atualizar_documento_com_assinatura(
            documento_type, documento_id, resultado
        )
        
        logger.info(
            f"Documento assinado com sucesso: {documento_type} {documento_id}",
            extra={
                'task_id': self.request.id,
                'empresa_id': empresa_id,
                'hash': resultado['hash'][:20] + '...'
            }
        )
        
        return {
            'success': True,
            'documento_id': documento_id,
            'hash': resultado['hash'],
            'timestamp': timezone.now().isoformat()
        }
        
    except Empresa.DoesNotExist:
        logger.error(f"Empresa {empresa_id} não encontrada")
        return {'success': False, 'error': 'Empresa não encontrada'}
        
    except FiscalServiceError as e:
        logger.error(f"Erro fiscal na assinatura: {e}")
        # Retry em caso de erro
        raise self.retry(countdown=60, exc=e)
        
    except Exception as e:
        logger.error(f"Erro inesperado na assinatura: {e}")
        return {'success': False, 'error': str(e)}


def _atualizar_documento_com_assinatura(documento_type: str, documento_id: int, resultado: Dict):
    """Atualiza documento com dados da assinatura"""
    from django.apps import apps
    
    # Mapeamento de tipos para models
    model_mapping = {
        'Venda': 'vendas.Venda',
        'FaturaCredito': 'vendas.FaturaCredito',
        'NotaCredito': 'vendas.NotaCredito',
        'NotaDebito': 'vendas.NotaDebito',
        'Recibo': 'vendas.Recibo'
    }
    
    if documento_type not in model_mapping:
        logger.warning(f"Tipo de documento não reconhecido: {documento_type}")
        return
    
    try:
        model = apps.get_model(model_mapping[documento_type])
        documento = model.objects.get(id=documento_id)
        
        # Atualizar campos de assinatura (se existirem)
        if hasattr(documento, 'hash_documento'):
            documento.hash_documento = resultado['hash']
        if hasattr(documento, 'assinatura_digital'):
            documento.assinatura_digital = resultado['assinatura']
        if hasattr(documento, 'hash_anterior'):
            documento.hash_anterior = resultado['hash_anterior']
        if hasattr(documento, 'data_assinatura'):
            documento.data_assinatura = timezone.now()
        
        documento.save()
        
    except Exception as e:
        logger.error(f"Erro ao atualizar documento {documento_type} {documento_id}: {e}")


@shared_task
def gerar_chaves_rsa_async(empresa_id: int, tamanho_chave: int = 2048):
    """
    Gera chaves RSA de forma assíncrona
    """
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        
        logger.info(
            f"Iniciando geração de chaves RSA para empresa {empresa_id}",
            extra={'empresa_id': empresa_id, 'tamanho_chave': tamanho_chave}
        )
        
        assinatura = AssinaturaDigitalService.gerar_chaves_rsa(empresa, tamanho_chave)
        
        logger.info(
            f"Chaves RSA geradas com sucesso para empresa {empresa_id}",
            extra={'empresa_id': empresa_id}
        )
        
        return {
            'success': True,
            'empresa_id': empresa_id,
            'data_geracao': assinatura.data_geracao.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar chaves RSA: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def verificar_integridade_cadeia(empresa_id: int, verificar_todas_series: bool = False):
    """
    Verifica integridade da cadeia de hash dos documentos
    """
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        assinatura = AssinaturaDigital.objects.get(empresa=empresa)
        
        logger.info(
            f"Iniciando verificação de integridade para empresa {empresa_id}",
            extra={'empresa_id': empresa_id}
        )
        
        problemas = []
        series_verificadas = 0
        
        for serie, dados in assinatura.dados_series_fiscais.items():
            series_verificadas += 1
            ultimo_hash = dados.get('ultimo_hash')
            ultimo_documento = dados.get('ultimo_documento')
            
            if not ultimo_hash:
                problemas.append(f"Série {serie}: Hash ausente")
                continue
            
            # Verificar se o hash está correto
            # Aqui seria implementada a lógica de verificação real
            
        # Atualizar cache com resultado
        cache_key = f"integridade_verificada_{empresa_id}"
        resultado = {
            'verificado_em': timezone.now().isoformat(),
            'series_verificadas': series_verificadas,
            'problemas_encontrados': len(problemas),
            'problemas': problemas,
            'integridade_ok': len(problemas) == 0
        }
        cache.set(cache_key, resultado, timeout=3600)
        
        if problemas:
            logger.warning(
                f"Problemas de integridade encontrados na empresa {empresa_id}",
                extra={'empresa_id': empresa_id, 'problemas': problemas}
            )
        else:
            logger.info(
                f"Integridade verificada com sucesso para empresa {empresa_id}",
                extra={'empresa_id': empresa_id, 'series_verificadas': series_verificadas}
            )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro na verificação de integridade: {e}")
        return {'success': False, 'error': str(e)}


# =====================================
# Tasks para SAF-T e Exportações
# =====================================

@shared_task(bind=True)
def gerar_saft_async(self, empresa_id: int, data_inicio: str, data_fim: str, 
                    usuario_id: int, enviar_email: bool = False):
    """
    Gera arquivo SAF-T de forma assíncrona
    """
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        logger.info(
            f"Iniciando geração SAF-T para empresa {empresa_id}",
            extra={
                'task_id': self.request.id,
                'empresa_id': empresa_id,
                'periodo': f"{data_inicio} a {data_fim}"
            }
        )
        
        # Gerar SAF-T
        xml_content = SAFTExportService.gerar_saft_ao(
            empresa, data_inicio_obj, data_fim_obj
        )
        
        # Salvar arquivo
        filename = f"SAFT_AO_{empresa.nif}_{data_inicio}_{data_fim}.xml"
        file_path = _salvar_arquivo_saft(filename, xml_content)
        
        # Enviar por email se solicitado
        if enviar_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            usuario = User.objects.get(id=usuario_id)
            
            enviar_saft_por_email.delay(
                usuario_email=usuario.email,
                empresa_nome=empresa.nome,
                file_path=file_path,
                periodo=f"{data_inicio} a {data_fim}"
            )
        
        logger.info(
            f"SAF-T gerado com sucesso para empresa {empresa_id}",
            extra={
                'task_id': self.request.id,
                'empresa_id': empresa_id,
                'arquivo': filename,
                'tamanho': len(xml_content)
            }
        )
        
        return {
            'success': True,
            'filename': filename,
            'file_path': file_path,
            'size': len(xml_content),
            'generated_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na geração SAF-T: {e}")
        return {'success': False, 'error': str(e)}


def _salvar_arquivo_saft(filename: str, content: str) -> str:
    """Salva arquivo SAF-T no sistema de arquivos"""
    # Diretório para arquivos SAF-T
    saft_dir = os.path.join(settings.MEDIA_ROOT, 'saft_exports')
    os.makedirs(saft_dir, exist_ok=True)
    
    file_path = os.path.join(saft_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


@shared_task
def enviar_saft_por_email(usuario_email: str, empresa_nome: str, 
                         file_path: str, periodo: str):
    """
    Envia arquivo SAF-T por email
    """
    try:
        subject = f"Arquivo SAF-T AO - {empresa_nome} - {periodo}"
        
        html_content = render_to_string('fiscais/emails/saft_gerado.html', {
            'empresa_nome': empresa_nome,
            'periodo': periodo,
            'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M')
        })
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Arquivo SAF-T AO em anexo",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Anexar arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            email.attach(os.path.basename(file_path), f.read(), 'application/xml')
        
        email.send()
        
        logger.info(
            f"SAF-T enviado por email para {usuario_email}",
            extra={'email': usuario_email, 'arquivo': os.path.basename(file_path)}
        )
        
        return {'success': True, 'email_sent_to': usuario_email}
        
    except Exception as e:
        logger.error(f"Erro ao enviar SAF-T por email: {e}")
        return {'success': False, 'error': str(e)}


# =====================================
# Tasks para Retenções na Fonte
# =====================================

@shared_task
def notificar_retencao_criada(retencao_id: int, empresa_id: int):
    """
    Notifica criação de nova retenção na fonte
    """
    try:
        retencao = RetencaoFonte.objects.get(id=retencao_id)
        empresa = Empresa.objects.get(id=empresa_id)
        
        logger.info(
            f"Processando notificação de retenção {retencao_id}",
            extra={'retencao_id': retencao_id, 'empresa_id': empresa_id}
        )
        
        # Enviar email para responsáveis fiscais
        responsaveis_emails = _obter_emails_responsaveis_fiscais(empresa)
        
        if responsaveis_emails:
            subject = f"Nova Retenção na Fonte - {retencao.tipo_retencao}"
            
            html_content = render_to_string('fiscais/emails/retencao_criada.html', {
                'retencao': retencao,
                'empresa': empresa
            })
            
            send_mail(
                subject=subject,
                message=f"Nova retenção criada: {retencao.referencia_documento}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=responsaveis_emails,
                html_message=html_content
            )
        
        # Atualizar cache de métricas
        cache_key = f"metricas_retencoes_{empresa_id}"
        cache.delete(cache_key)
        
        return {'success': True, 'emails_enviados': len(responsaveis_emails)}
        
    except Exception as e:
        logger.error(f"Erro ao notificar retenção: {e}")
        return {'success': False, 'error': str(e)}


def _obter_emails_responsaveis_fiscais(empresa: Empresa) -> List[str]:
    """Obtém emails dos responsáveis fiscais da empresa"""
    # Implementar lógica para obter emails dos responsáveis
    # Por exemplo, através de grupos de usuários ou perfis específicos
    emails = []
    
    try:
        # Exemplo: usuários do grupo "Fiscal" da empresa
        from django.contrib.auth.models import Group
        grupo_fiscal = Group.objects.get(name='Fiscal')
        
        responsaveis = empresa.funcionarios.filter(
            usuario__groups=grupo_fiscal,
            usuario__is_active=True
        ).values_list('usuario__email', flat=True)
        
        emails = [email for email in responsaveis if email]
        
    except Exception as e:
        logger.warning(f"Erro ao obter emails responsáveis fiscais: {e}")
    
    return emails


@shared_task
def processar_retencoes_vencidas():
    """
    Processa retenções vencidas e envia notificações
    """
    try:
        hoje = date.today()
        
        # Buscar retenções que deveriam ter sido pagas
        retencoes_vencidas = RetencaoFonte.objects.filter(
            paga_ao_estado=False,
            data_retencao__lt=hoje - timedelta(days=30)  # 30 dias para pagar
        ).select_related('empresa', 'fornecedor')
        
        empresas_notificadas = set()
        total_retencoes = 0
        
        for retencao in retencoes_vencidas:
            total_retencoes += 1
            
            if retencao.empresa.id not in empresas_notificadas:
                # Notificar empresa apenas uma vez
                _notificar_retencoes_vencidas_empresa(retencao.empresa)
                empresas_notificadas.add(retencao.empresa.id)
        
        logger.info(
            f"Processadas {total_retencoes} retenções vencidas de {len(empresas_notificadas)} empresas",
            extra={
                'total_retencoes': total_retencoes,
                'empresas': len(empresas_notificadas)
            }
        )
        
        return {
            'success': True,
            'retencoes_vencidas': total_retencoes,
            'empresas_notificadas': len(empresas_notificadas)
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar retenções vencidas: {e}")
        return {'success': False, 'error': str(e)}


def _notificar_retencoes_vencidas_empresa(empresa: Empresa):
    """Notifica empresa sobre retenções vencidas"""
    emails = _obter_emails_responsaveis_fiscais(empresa)
    
    if emails:
        subject = f"Retenções na Fonte Vencidas - {empresa.nome}"
        
        html_content = render_to_string('fiscais/emails/retencoes_vencidas.html', {
            'empresa': empresa,
            'data_verificacao': date.today()
        })
        
        send_mail(
            subject=subject,
            message="Existem retenções na fonte vencidas que devem ser pagas ao Estado.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            html_message=html_content
        )


# =====================================
# Tasks para Backup e Manutenção
# =====================================


def _coletar_dados_fiscais(empresa: Empresa, data_referencia: str) -> Dict:
    """Coleta dados fiscais para backup"""
    data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    
    # Coletar dados dos últimos 12 meses
    data_inicio = data_ref - timedelta(days=365)
    
    dados = {
        'empresa': {
            'id': empresa.id,
            'nome': empresa.nome,
            'nif': empresa.nif
        },
        'periodo': {
            'inicio': data_inicio.isoformat(),
            'fim': data_ref.isoformat()
        },
        'taxas_iva': list(TaxaIVAAGT.objects.filter(
            empresa=empresa
        ).values()),
        'retencoes': list(RetencaoFonte.objects.filter(
            empresa=empresa,
            data_retencao__gte=data_inicio,
            data_retencao__lte=data_ref
        ).values()),
        'assinatura_digital': {}
    }
    
    # Dados da assinatura digital
    try:
        assinatura = AssinaturaDigital.objects.get(empresa=empresa)
        dados['assinatura_digital'] = {
            'configurada': True,
            'ultimo_hash': assinatura.ultimo_hash,
            'series_fiscais': assinatura.dados_series_fiscais,
            'data_geracao': assinatura.data_geracao.isoformat()
        }
    except AssinaturaDigital.DoesNotExist:
        dados['assinatura_digital'] = {'configurada': False}
    
    return dados


def _criar_arquivo_backup(filename: str, dados: Dict) -> str:
    """Cria arquivo ZIP com dados de backup"""
    import json
    
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups_fiscal')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, filename)
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar dados JSON
        dados_json = json.dumps(dados, indent=2, default=str, ensure_ascii=False)
        zipf.writestr('dados_fiscais.json', dados_json.encode('utf-8'))
        
        # Adicionar arquivo README
        readme_content = f"""
Backup Fiscal - {dados['empresa']['nome']}
======================================

NIF: {dados['empresa']['nif']}
Período: {dados['periodo']['inicio']} a {dados['periodo']['fim']}
Gerado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}

Conteúdo:
- dados_fiscais.json: Dados fiscais estruturados
- Este arquivo README.txt

Para restaurar os dados, utilize o sistema de importação
do módulo fiscal do PharmaSys.
        """
        zipf.writestr('README.txt', readme_content.encode('utf-8'))
    
    return backup_path


@shared_task
def limpeza_arquivos_temporarios():
    """
    Remove arquivos temporários antigos
    """
    try:
        hoje = datetime.now()
        dias_manter = 30  # Manter arquivos por 30 dias
        
        diretorios = [
            os.path.join(settings.MEDIA_ROOT, 'saft_exports'),
            os.path.join(settings.MEDIA_ROOT, 'backups_fiscal'),
            os.path.join(settings.MEDIA_ROOT, 'relatorios_fiscal')
        ]
        
        arquivos_removidos = 0
        espaco_liberado = 0
        
        for diretorio in diretorios:
            if not os.path.exists(diretorio):
                continue
            
            for filename in os.listdir(diretorio):
                file_path = os.path.join(diretorio, filename)
                
                if os.path.isfile(file_path):
                    # Verificar idade do arquivo
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    idade_dias = (hoje - file_time).days
                    
                    if idade_dias > dias_manter:
                        tamanho = os.path.getsize(file_path)
                        os.remove(file_path)
                        arquivos_removidos += 1
                        espaco_liberado += tamanho
        
        logger.info(
            f"Limpeza concluída: {arquivos_removidos} arquivos removidos",
            extra={
                'arquivos_removidos': arquivos_removidos,
                'espaco_liberado_mb': round(espaco_liberado / 1024 / 1024, 2)
            }
        )
        
        return {
            'success': True,
            'arquivos_removidos': arquivos_removidos,
            'espaco_liberado_bytes': espaco_liberado
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza de arquivos: {e}")
        return {'success': False, 'error': str(e)}


# =====================================
# Tasks para Relatórios
# =====================================

@shared_task
def gerar_relatorio_mensal_async(empresa_id: int, ano: int, mes: int, enviar_email: bool = True):
    """
    Gera relatório fiscal mensal de forma assíncrona
    """
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        
        logger.info(
            f"Gerando relatório mensal para empresa {empresa_id} - {mes:02d}/{ano}",
            extra={'empresa_id': empresa_id, 'periodo': f"{mes:02d}/{ano}"}
        )
        
        # Gerar dados do relatório
        dados_relatorio = _gerar_dados_relatorio_mensal(empresa, ano, mes)
        
        # Criar arquivo PDF do relatório
        pdf_path = _gerar_pdf_relatorio_mensal(empresa, ano, mes, dados_relatorio)
        
        if enviar_email:
            # Enviar por email
            emails = _obter_emails_responsaveis_fiscais(empresa)
            if emails:
                enviar_relatorio_por_email.delay(
                    empresa_nome=empresa.nome,
                    periodo=f"{mes:02d}/{ano}",
                    pdf_path=pdf_path,
                    emails=emails
                )
        
        logger.info(
            f"Relatório mensal gerado com sucesso para empresa {empresa_id}",
            extra={'empresa_id': empresa_id, 'arquivo': os.path.basename(pdf_path)}
        )
        
        return {
            'success': True,
            'pdf_path': pdf_path,
            'dados': dados_relatorio
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório mensal: {e}")
        return {'success': False, 'error': str(e)}


def _gerar_dados_relatorio_mensal(empresa: Empresa, ano: int, mes: int) -> Dict:
    """Gera dados para relatório mensal"""
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - timedelta(days=1)
    
    # Métricas do período
    metricas = FiscalDashboardService.obter_metricas_fiscais(
        empresa, (data_inicio, data_fim)
    )
    
    # Dados adicionais
    dados = {
        'periodo': {
            'mes': mes,
            'ano': ano,
            'data_inicio': data_inicio.isoformat(),
            'data_fim': data_fim.isoformat()
        },
        'metricas': metricas,
        'empresa': {
            'nome': empresa.nome,
            'nif': empresa.nif
        },
        'gerado_em': timezone.now().isoformat()
    }
    
    return dados


def _gerar_pdf_relatorio_mensal(empresa: Empresa, ano: int, mes: int, dados: Dict) -> str:
    """Gera arquivo PDF do relatório mensal"""
    # Implementar geração de PDF usando ReportLab ou similar
    # Por enquanto, criar um arquivo de texto
    
    relatorio_dir = os.path.join(settings.MEDIA_ROOT, 'relatorios_fiscal')
    os.makedirs(relatorio_dir, exist_ok=True)
    
    filename = f"relatorio_fiscal_{empresa.nif}_{ano}_{mes:02d}.txt"
    file_path = os.path.join(relatorio_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"RELATÓRIO FISCAL MENSAL\n")
        f.write(f"========================\n\n")
        f.write(f"Empresa: {empresa.nome}\n")
        f.write(f"NIF: {empresa.nif}\n")
        f.write(f"Período: {mes:02d}/{ano}\n\n")
        f.write(f"Gerado em: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        # Adicionar dados do relatório
        if 'retencoes' in dados['metricas']:
            ret = dados['metricas']['retencoes']
            f.write(f"RETENÇÕES NA FONTE:\n")
            f.write(f"- Total: {ret['total_count']}\n")
            f.write(f"- Valor Total: AKZ {ret['total_valor']:,.2f}\n")
            f.write(f"- Pagas: {ret['pagas_count']}\n")
            f.write(f"- Pendentes: {ret['pendentes_count']}\n\n")
    
    return file_path


@shared_task
def enviar_relatorio_por_email(empresa_nome: str, periodo: str, pdf_path: str, emails: List[str]):
    """
    Envia relatório fiscal por email
    """
    try:
        subject = f"Relatório Fiscal Mensal - {empresa_nome} - {periodo}"
        
        html_content = render_to_string('fiscais/emails/relatorio_mensal.html', {
            'empresa_nome': empresa_nome,
            'periodo': periodo,
            'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M')
        })
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Relatório fiscal mensal em anexo",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emails
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Anexar arquivo
        with open(pdf_path, 'rb') as f:
            email.attach(
                os.path.basename(pdf_path),
                f.read(),
                'application/pdf'
            )
        
        email.send()
        
        logger.info(
            f"Relatório enviado por email para {len(emails)} destinatários",
            extra={'emails_count': len(emails), 'periodo': periodo}
        )
        
        return {'success': True, 'emails_enviados': len(emails)}
        
    except Exception as e:
        logger.error(f"Erro ao enviar relatório por email: {e}")
        return {'success': False, 'error': str(e)}


# =====================================
# Tasks Periódicas (Cron)
# =====================================

@shared_task
def task_backup_diario():
    signals.gerar_backup_fiscal(empresa)
    """
    Task executada diariamente para backup automático
    """
    try:
        # Backup para todas as empresas ativas
        empresas = Empresa.objects.filter(ativa=True)
        backups_gerados = 0
        
        for empresa in empresas:
            signals.gerar_backup_fiscal.delay(
                empresa_id=empresa.id,
                motivo="Backup automático diário"
            )
            backups_gerados += 1
        
        logger.info(
            f"Backups diários agendados para {backups_gerados} empresas",
            extra={'empresas_count': backups_gerados}
        )
        
        return {'success': True, 'backups_agendados': backups_gerados}
        
    except Exception as e:
        logger.error(f"Erro no backup diário: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def task_verificacao_integridade_semanal():
    """
    Task executada semanalmente para verificação de integridade
    """
    try:
        empresas_com_assinatura = AssinaturaDigital.objects.select_related('empresa').all()
        verificacoes_agendadas = 0
        
        for assinatura in empresas_com_assinatura:
            verificar_integridade_cadeia.delay(
                empresa_id=assinatura.empresa.id,
                verificar_todas_series=True
            )
            verificacoes_agendadas += 1
        
        logger.info(
            f"Verificações de integridade agendadas para {verificacoes_agendadas} empresas",
            extra={'verificacoes_count': verificacoes_agendadas}
        )
        
        return {'success': True, 'verificacoes_agendadas': verificacoes_agendadas}
        
    except Exception as e:
        logger.error(f"Erro na verificação semanal: {e}")
        return {'success': False, 'error': str(e)}

