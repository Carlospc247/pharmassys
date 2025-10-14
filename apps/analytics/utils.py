import requests
from django.conf import settings
# Lembre-se que este import requer a biblioteca 'django-user-agents'
# pip install django-user-agents
# apps/analytics/utils.py
from django.utils import timezone
from apps.analytics.models import EventoAnalytics
from django.utils import timezone
from datetime import timedelta
from .models import EventoAnalytics, AuditoriaAlteracao, AlertaInteligente
import user_agents


def get_geolocation_data(ip_address):
    """
    Obtém dados de geolocalização (país e cidade) para um dado IP
    usando a API gratuita e sem necessidade de chave do ip-api.com.

    Retorna: (codigo_pais, nome_cidade) ou (None, None) em caso de falha.
    """
    # Ignora IPs locais/privados que não podem ser geolocalizados
    if not ip_address or ip_address == '127.0.0.1' or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return None, None

    try:
        # URL do endpoint da API. Pedimos apenas os campos que nos interessam para ser mais rápido.
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,countryCode,city"
        
        # Faz o pedido à API com um timeout de 2 segundos para não atrasar o seu sistema
        response = requests.get(url, timeout=2)
        
        # Lança um erro se a API estiver em baixo (ex: erro 500)
        response.raise_for_status()  
        
        data = response.json()
        
        if data.get('status') == 'success':
            country_code = data.get('countryCode')  # Ex: 'AO' para Angola
            city = data.get('city')            # Ex: 'Luanda'
            return country_code, city
        else:
            return None, None

    except requests.exceptions.RequestException:
        # Captura erros de rede (sem internet, timeout, etc.) e continua sem falhar o sistema
        # Idealmente, aqui você teria um log para o administrador do sistema
        return None, None

def parse_user_agent_string(ua_string):
    """
    Recebe uma string de user-agent e retorna um dicionário com a informação analisada.
    """
    if not ua_string:
        return {}
    
    try:
        user_agent = user_agents.parse(ua_string)
        return {
            'browser': user_agent.browser.family,
            'os': user_agent.os.family,
            'device': user_agent.device.family,
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc,
        }
    except Exception:
        return {}





def registrar_evento(
    empresa,
    categoria,
    acao,
    usuario=None,
    request=None,
    label="",
    propriedades=None,
    valor=None,
):
    """
    Registra um evento de analytics no banco de dados.
    """

    propriedades = propriedades or {}

    ip = request.META.get("REMOTE_ADDR") if request else None
    user_agent_string = request.META.get("HTTP_USER_AGENT") if request else ""
    url = request.build_absolute_uri() if request else ""
    referrer = request.META.get("HTTP_REFERER", "") if request else ""

    # parse do user agent
    user_agent_info = parse_user_agent_string(user_agent_string)

    # geolocalização
    pais, cidade = get_geolocation_data(ip) if ip else (None, None)

    evento = EventoAnalytics.objects.create(
        empresa=empresa,
        usuario=usuario if usuario and usuario.is_authenticated else None,
        categoria=categoria,
        acao=acao,
        label=label,
        propriedades=propriedades,
        valor=valor,
        ip_address=ip,
        user_agent=user_agent_string,
        url=url,
        referrer=referrer,
        pais=pais or "",
        cidade=cidade or "",
        timestamp=timezone.now(),
    )

    return evento



def calcular_metricas():
    """
    Retorna métricas principais do sistema de analytics:
    totais, últimas 24h, última semana e último mês.
    """
    agora = timezone.now()

    # Intervalos de tempo
    ultimas_24h = agora - timedelta(hours=24)
    ultima_semana = agora - timedelta(days=7)
    ultimo_mes = agora - timedelta(days=30)

    # ===== Eventos =====
    total_eventos = EventoAnalytics.objects.count()
    eventos_24h = EventoAnalytics.objects.filter(timestamp__gte=ultimas_24h).count()
    eventos_semana = EventoAnalytics.objects.filter(timestamp__gte=ultima_semana).count()
    eventos_mes = EventoAnalytics.objects.filter(timestamp__gte=ultimo_mes).count()

    # ===== Auditorias =====
    total_auditorias = AuditoriaAlteracao.objects.count()
    auditorias_24h = AuditoriaAlteracao.objects.filter(data__gte=ultimas_24h).count()
    auditorias_semana = AuditoriaAlteracao.objects.filter(data__gte=ultima_semana).count()
    auditorias_mes = AuditoriaAlteracao.objects.filter(data__gte=ultimo_mes).count()

    # ===== Alertas =====
    total_alertas = AlertaInteligente.objects.count()
    alertas_24h = AlertaInteligente.objects.filter(criado_em__gte=ultimas_24h).count()
    alertas_semana = AlertaInteligente.objects.filter(criado_em__gte=ultima_semana).count()
    alertas_mes = AlertaInteligente.objects.filter(criado_em__gte=ultimo_mes).count()

    # Retorno organizado
    return {
        "eventos": {
            "total": total_eventos,
            "24h": eventos_24h,
            "semana": eventos_semana,
            "mes": eventos_mes,
        },
        "auditorias": {
            "total": total_auditorias,
            "24h": auditorias_24h,
            "semana": auditorias_semana,
            "mes": auditorias_mes,
        },
        "alertas": {
            "total": total_alertas,
            "24h": alertas_24h,
            "semana": alertas_semana,
            "mes": alertas_mes,
        },
    }


def gerar_alerta(empresa, tipo, mensagem, severidade="info"):
    """
    Cria um alerta no sistema.
    """
    return AlertaInteligente.objects.create(
        empresa=empresa,
        tipo=tipo,
        mensagem=mensagem,
        severidade=severidade
    )


def get_client_ip(request):
    """
    Retorna o IP real do cliente a partir do request,
    mesmo se estiver atrás de proxy ou load balancer.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


from user_agents import parse

def get_user_agent(request):
    """
    Extrai e retorna o user agent do request (ex: navegador, SO, dispositivo).
    """
    ua_string = request.META.get("HTTP_USER_AGENT", "")
    if not ua_string:
        return None

    user_agent = parse(ua_string)
    return {
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "device": user_agent.device.family or "Unknown"
    }


import requests

def detectar_localizacao(ip_address):
    """
    Detecta localização aproximada a partir do IP do cliente.
    Usa API pública ipapi.co (pode trocar por outra).
    """
    if ip_address in ("127.0.0.1", "::1"):
        return {"ip": ip_address, "cidade": "Localhost", "pais": "Desconhecido"}

    try:
        url = f"https://ipapi.co/{ip_address}/json/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": ip_address,
                "cidade": data.get("city", "Desconhecido"),
                "regiao": data.get("region", "Desconhecido"),
                "pais": data.get("country_name", "Desconhecido"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
            }
    except Exception:
        pass

    return {"ip": ip_address, "cidade": "Desconhecido", "pais": "Desconhecido"}


