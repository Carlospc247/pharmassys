from django.apps import AppConfig


class ComandasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'

    def ready(self):
            # Importa os sinais para que sejam registados quando a app iniciar
            import apps.analytics.signals
