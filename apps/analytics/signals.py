from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .services import AnalyticsService

@receiver(user_logged_in)
def registrar_login_sucesso(sender, request, user, **kwargs):
    """
    Esta função é chamada automaticamente sempre que um utilizador faz login.
    """
    if hasattr(user, 'funcionario') and user.funcionario.empresa:
        empresa = user.funcionario.empresa
        
        # Usa o serviço de analytics para registar o evento
        analytics_service = AnalyticsService(empresa=empresa, usuario=user)
        analytics_service.track_login(request)
