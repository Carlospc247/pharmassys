# tests/test_produtos.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Empresa, Loja
from apps.produtos.models import Produto, Categoria, Fabricante
from decimal import Decimal

User = get_user_model()

class ProdutoTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nome="Farmácia Teste",
            nif="12.345.678/0001-90",
            razao_social="Farmácia Teste Ltda"
        )
        
        self.categoria = Categoria.objects.create(
            nome="Medicamentos",
            empresa=self.empresa
        )
        
        self.fabricante = Fabricante.objects.create(
            nome="EMS",
            nif="12.345.678/0001-91",
            empresa=self.empresa
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            empresa=self.empresa
        )
    
    def test_criacao_produto(self):
        produto = Produto.objects.create(
            codigo_barras="7891234567890",
            nome_comercial="Dipirona Gotas",
            categoria=self.categoria,
            fabricante=self.fabricante,
            tipo="medicamento",
            preco_venda=Decimal('15.90'),
            preco_custo=Decimal('8.50'),
            empresa=self.empresa
        )
        
        self.assertEqual(produto.nome_comercial, "Dipirona Gotas")
        self.assertTrue(produto.margem_lucro > 0)
    
    def test_calculo_margem_lucro(self):
        produto = Produto(
            codigo_barras="7891234567891",
            nome_comercial="Paracetamol",
            categoria=self.categoria,
            fabricante=self.fabricante,
            tipo="medicamento",
            preco_venda=Decimal('10.00'),
            preco_custo=Decimal('5.00'),
            empresa=self.empresa
        )
        produto.save()
        
        # Margem deveria ser 100%
        self.assertEqual(produto.margem_lucro, Decimal('100.00'))

"""
<!-- Exemplos de uso nos templates -->

<!-- Dashboard -->
<a href="{% url 'core:dashboard' %}">Dashboard</a>

<!-- Empresas -->
<a href="{% url 'core:empresa_lista' %}">Listar Empresas</a>
<a href="{% url 'core:empresa_criar' %}">Nova Empresa</a>
<a href="{% url 'core:empresa_detalhe' empresa.pk %}">Ver Empresa</a>
<a href="{% url 'core:empresa_editar' empresa.pk %}">Editar</a>

<!-- Lojas -->
<a href="{% url 'core:loja_lista' %}">Listar Lojas</a>
<a href="{% url 'core:loja_criar' %}">Nova Loja</a>
<a href="{% url 'core:loja_detalhe' loja.pk %}">Ver Loja</a>

<!-- Usuários -->
<a href="{% url 'core:usuario_lista' %}">Listar Usuários</a>
<a href="{% url 'core:perfil' %}">Meu Perfil</a>

<!-- Autenticação -->
<a href="{% url 'core:logout' %}">Sair</a>

<!-- Com a versão alternativa (namespaced) -->
<a href="{% url 'core:empresa:lista' %}">Listar Empresas</a>
<a href="{% url 'core:loja:criar' %}">Nova Loja</a>
"""


