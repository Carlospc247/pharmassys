#apps/fiscal/apps.py
from django.apps import AppConfig

class FiscalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fiscal'
    verbose_name = 'Gestão Fiscal'
    
    def ready(self):
        """
        Configurações executadas quando a app está pronta
        """
        # Importar signals se houver
        try:
            import apps.fiscal.signals
        except ImportError:
            pass
        
        # Registrar tasks do Celery se houver
        try:
            import apps.fiscal.tasks
        except ImportError:
            pass