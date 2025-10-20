from django.test import SimpleTestCase
from django.urls import reverse

# A classe de teste deve herdar de 'SimpleTestCase' para testar apenas URLs sem base de dados
class URLTests(SimpleTestCase):
    
    # Este método de teste específico verifica se a URL 'suporte' está definida
    def test_suporte_url_exists(self):
        # Tenta reverter a URL. Se falhar, levanta NoReverseMatch
        try:
            # A função reverse() procura pelo nome 'suporte' nos seus patterns de URL
            url = reverse('suporte')
            # Confirma que a URL foi encontrada (não None)
            self.assertIsNotNone(url) 
        except Exception as e:
            # Se ocorrer NoReverseMatch, o teste falha com uma mensagem clara
            self.fail(f"NoReverseMatch para 'suporte': A URL não está definida corretamente ou o nome está errado. Erro: {e}")
            
