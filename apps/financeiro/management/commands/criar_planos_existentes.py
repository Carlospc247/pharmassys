# apps/financeiro/management/commands/criar_planos_existentes.py
from django.core.management.base import BaseCommand
from apps.core.models import Empresa
from apps.financeiro.signals import criar_plano_contas_basico

class Command(BaseCommand):
    help = "Cria planos de contas padrão para empresas existentes que ainda não têm"

    def handle(self, *args, **kwargs):
        empresas = Empresa.objects.all()
        for empresa in empresas:
            if not empresa.planocontas_set.exists():
                criar_plano_contas_basico(sender=Empresa, instance=empresa, created=True)
                self.stdout.write(self.style.SUCCESS(f"Planos criados para empresa: {empresa.nome}"))
            else:
                self.stdout.write(f"Empresa já possui plano: {empresa.nome}")

# Esse script cria plano contas para empresas já existentes.

