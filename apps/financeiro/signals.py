# apps/financeiro/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.models import Empresa
from apps.financeiro.models import PlanoContas


@receiver(post_save, sender=Empresa)
def criar_plano_contas_basico(sender, instance, created, **kwargs):
    if created:
        # Só cria se a empresa ainda não tiver contas
        if not PlanoContas.objects.filter(empresa=instance).exists():

            # -------------------
            # ATIVOS
            # -------------------
            ativo = PlanoContas.objects.create(
                codigo="1",
                nome="Ativos",
                tipo_conta="ativo",
                natureza="debito",
                aceita_lancamento=False,
                nivel=1,
                empresa=instance
            )
            ativo_circulante = PlanoContas.objects.create(
                codigo="1.1",
                nome="Ativo Circulante",
                tipo_conta="ativo",
                natureza="debito",
                aceita_lancamento=False,
                conta_pai=ativo,
                nivel=2,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="1.1.1",
                nome="Caixa",
                tipo_conta="ativo",
                natureza="debito",
                aceita_lancamento=True,
                conta_pai=ativo_circulante,
                nivel=3,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="1.1.2",
                nome="Bancos",
                tipo_conta="ativo",
                natureza="debito",
                aceita_lancamento=True,
                conta_pai=ativo_circulante,
                nivel=3,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="1.1.3",
                nome="Clientes",
                tipo_conta="ativo",
                natureza="debito",
                aceita_lancamento=True,
                conta_pai=ativo_circulante,
                nivel=3,
                empresa=instance
            )

            # -------------------
            # PASSIVOS
            # -------------------
            passivo = PlanoContas.objects.create(
                codigo="2",
                nome="Passivos",
                tipo_conta="passivo",
                natureza="credito",
                aceita_lancamento=False,
                nivel=1,
                empresa=instance
            )
            passivo_circulante = PlanoContas.objects.create(
                codigo="2.1",
                nome="Passivo Circulante",
                tipo_conta="passivo",
                natureza="credito",
                aceita_lancamento=False,
                conta_pai=passivo,
                nivel=2,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="2.1.1",
                nome="Fornecedores",
                tipo_conta="passivo",
                natureza="credito",
                aceita_lancamento=True,
                conta_pai=passivo_circulante,
                nivel=3,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="2.1.2",
                nome="Salários a Pagar",
                tipo_conta="passivo",
                natureza="credito",
                aceita_lancamento=True,
                conta_pai=passivo_circulante,
                nivel=3,
                empresa=instance
            )

            # -------------------
            # PATRIMÔNIO LÍQUIDO
            # -------------------
            pl = PlanoContas.objects.create(
                codigo="3",
                nome="Patrimônio Líquido",
                tipo_conta="patrimonio",
                natureza="credito",
                aceita_lancamento=False,
                nivel=1,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="3.1",
                nome="Capital Social",
                tipo_conta="patrimonio",
                natureza="credito",
                aceita_lancamento=True,
                conta_pai=pl,
                nivel=2,
                empresa=instance
            )

            # -------------------
            # RECEITAS
            # -------------------
            receita = PlanoContas.objects.create(
                codigo="4",
                nome="Receitas",
                tipo_conta="receita",
                natureza="credito",
                aceita_lancamento=False,
                nivel=1,
                empresa=instance
            )
            receita_op = PlanoContas.objects.create(
                codigo="4.1",
                nome="Receitas Operacionais",
                tipo_conta="receita",
                natureza="credito",
                aceita_lancamento=False,
                conta_pai=receita,
                nivel=2,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="4.1.1",
                nome="Receita de Vendas",
                tipo_conta="receita",
                natureza="credito",
                aceita_lancamento=True,
                conta_pai=receita_op,
                nivel=3,
                empresa=instance
            )

            # -------------------
            # DESPESAS
            # -------------------
            despesa = PlanoContas.objects.create(
                codigo="5",
                nome="Despesas",
                tipo_conta="despesa",
                natureza="debito",
                aceita_lancamento=False,
                nivel=1,
                empresa=instance
            )
            despesa_op = PlanoContas.objects.create(
                codigo="5.1",
                nome="Despesas Operacionais",
                tipo_conta="despesa",
                natureza="debito",
                aceita_lancamento=False,
                conta_pai=despesa,
                nivel=2,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="5.1.1",
                nome="Despesas Administrativas",
                tipo_conta="despesa",
                natureza="debito",
                aceita_lancamento=True,
                conta_pai=despesa_op,
                nivel=3,
                empresa=instance
            )
            PlanoContas.objects.create(
                codigo="5.1.2",
                nome="Despesas com Vendas",
                tipo_conta="despesa",
                natureza="debito",
                aceita_lancamento=True,
                conta_pai=despesa_op,
                nivel=3,
                empresa=instance
            )

