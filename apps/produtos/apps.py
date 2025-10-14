from django.apps import AppConfig


class ProdutosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.produtos'

    def ready(self):
        # Importa o módulo de signals para que ele seja registrado.
        import apps.produtos.signals


