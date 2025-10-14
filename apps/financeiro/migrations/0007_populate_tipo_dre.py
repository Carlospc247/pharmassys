from django.db import migrations

def populate_tipo_dre(apps, schema_editor):
    CategoriaFinanceira = apps.get_model('financeiro', 'CategoriaFinanceira')

    # Mapear nomes conhecidos para o tipo_dre correspondente
    mapping = {
        'Vendas': 'entrada',
        'Serviços': 'entrada',
        'Impostos': 'deducao',
        'ICMS': 'deducao',
        'Custo Mercadorias': 'custo',
        'Salários': 'despesa',
        'Aluguel': 'despesa',
        'Energia': 'despesa',
        'Juros Bancários': 'financeiro',
    }

    for categoria in CategoriaFinanceira.objects.all():
        # Usar mapping se encontrar, senão default 'outros'
        tipo = mapping.get(categoria.nome, 'outros')
        categoria.tipo_dre = tipo
        categoria.save(update_fields=['tipo_dre'])

def reverse_func(apps, schema_editor):
    # Caso precise reverter, deixamos tudo como NULL
    CategoriaFinanceira = apps.get_model('financeiro', 'CategoriaFinanceira')
    CategoriaFinanceira.objects.update(tipo_dre=None)

class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0006_categoriafinanceira_tipo_dre_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_tipo_dre, reverse_func),
    ]
