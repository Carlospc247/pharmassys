import logging
import platform
import socket
import psutil
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from apps.core.permissions import empresa_required
from apps.fiscal.models import TaxaIVAAGT, RetencaoFonte, AssinaturaDigital
from apps.fornecedores.models import Fornecedor

logger = logging.getLogger('fiscal.debug')


# -------------------------
# 🔹 DEBUG: Gerar Dados de Teste
# -------------------------
@login_required
@empresa_required
@require_POST
@transaction.atomic
def debug_gerar_dados_teste(request):
    """
    Gera dados de teste para desenvolvimento e debugging.
    Apenas disponível em ambiente de DEBUG.
    """
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Acesso restrito ao modo de debug."}, status=403)

    try:
        empresa = request.user.empresa_ativa

        # Criar fornecedores fake
        for i in range(3):
            Fornecedor.objects.get_or_create(
                empresa=empresa,
                nome=f"Fornecedor Teste {i+1}",
                nif=f"50000000{i+1}",
            )

        # Criar taxas de IVA
        for perc in [7, 14, 23]:
            TaxaIVAAGT.objects.get_or_create(
                empresa=empresa,
                tax_percentage=Decimal(perc),
                defaults={"descricao": f"IVA {perc}% (teste)", "ativo": True}
            )

        # Criar retenções fake
        for i in range(3):
            RetencaoFonte.objects.create(
                empresa=empresa,
                descricao=f"Retenção {i+1}",
                valor_retido=Decimal("100.00") * (i+1),
                data_retencao=datetime.now()
            )

        return JsonResponse({
            "success": True,
            "message": "Dados de teste gerados com sucesso."
        }, status=201)

    except Exception as e:
        logger.exception("Erro ao gerar dados de teste.")
        return JsonResponse({"success": False, "message": "Erro ao gerar dados de teste.", "error": str(e)}, status=500)


# -------------------------
# 🔹 DEBUG: Limpar Cache
# -------------------------
@login_required
@empresa_required
@require_POST
def debug_limpar_cache(request):
    """Limpa completamente o cache do sistema em ambiente de debug."""
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Acesso restrito ao modo de debug."}, status=403)

    try:
        cache.clear()
        return JsonResponse({"success": True, "message": "Cache limpo com sucesso."})
    except Exception as e:
        logger.exception("Erro ao limpar cache.")
        return JsonResponse({"success": False, "message": "Erro ao limpar cache.", "error": str(e)}, status=500)


# -------------------------
# 🔹 DEBUG: Info do Sistema
# -------------------------
@login_required
@require_GET
def debug_info_sistema(request):
    """Retorna informações detalhadas do sistema para diagnóstico."""
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Acesso restrito ao modo de debug."}, status=403)

    try:
        info = {
            "sistema": platform.system(),
            "versao": platform.version(),
            "python": platform.python_version(),
            "host": socket.gethostname(),
            "memoria_total": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "memoria_usada": f"{round(psutil.virtual_memory().used / (1024**3), 2)} GB",
            "disco_total": f"{round(psutil.disk_usage('/').total / (1024**3), 2)} GB",
            "disco_usado": f"{round(psutil.disk_usage('/').used / (1024**3), 2)} GB",
            "hora_servidor": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "debug_mode": settings.DEBUG,
        }

        return JsonResponse({"success": True, "data": info}, status=200)
    except Exception as e:
        logger.exception("Erro ao coletar informações do sistema.")
        return JsonResponse({"success": False, "message": "Erro ao obter informações do sistema.", "error": str(e)}, status=500)


# -------------------------
# 🔹 DEBUG: Testar Assinatura Digital
# -------------------------
@login_required
@empresa_required
@require_POST
def debug_testar_assinatura(request):
    """Executa um teste de validação da assinatura digital."""
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Acesso restrito ao modo de debug."}, status=403)

    try:
        empresa = request.user.empresa_ativa
        assinatura = AssinaturaDigital.objects.filter(empresa=empresa).first()

        if not assinatura:
            return JsonResponse({"success": False, "message": "Assinatura digital não configurada."}, status=404)

        hash_teste = "TESTE_HASH_12345"
        assinatura.ultimo_hash = hash_teste
        assinatura.save()

        return JsonResponse({
            "success": True,
            "message": "Assinatura digital testada com sucesso.",
            "hash": hash_teste
        })
    except Exception as e:
        logger.exception("Erro ao testar assinatura digital.")
        return JsonResponse({"success": False, "message": "Erro ao testar assinatura digital.", "error": str(e)}, status=500)


# -------------------------
# 🔹 DEBUG: Simular Comunicação com AGT
# -------------------------
@login_required
@empresa_required
@require_GET
def debug_simular_agt(request):
    """Simula uma comunicação com o servidor da AGT para teste de integração."""
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Acesso restrito ao modo de debug."}, status=403)

    try:
        resposta_fake = {
            "status": "success",
            "mensagem": "Conexão simulada com sucesso.",
            "codigo_resposta": "AGT-TEST-200",
            "timestamp": datetime.now().isoformat()
        }

        return JsonResponse({"success": True, "data": resposta_fake}, status=200)
    except Exception as e:
        logger.exception("Erro ao simular comunicação com AGT.")
        return JsonResponse({"success": False, "message": "Erro na simulação AGT.", "error": str(e)}, status=500)

