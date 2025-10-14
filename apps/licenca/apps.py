from django.apps import AppConfig


class LicencaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.licenca'


"""# apps/licenca/apps.py
from django.apps import AppConfig

class LicencaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.licenca'
    verbose_name = 'Sistema de Licenciamento'
    
    def ready(self):
        # Importa signals se necessário
        try:
            import apps.licenca.signals
        except ImportError:
            pass"""