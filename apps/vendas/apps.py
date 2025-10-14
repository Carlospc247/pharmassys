from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vendas'

    def ready(self):
        import apps.vendas.signals  # 👈 ativa o signal