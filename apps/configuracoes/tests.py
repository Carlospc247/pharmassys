# configuracoes/tests.py

from django.test import SimpleTestCase
from django.urls import reverse

# A classe deve ser importável e herdar de TestCase
class URLTests(SimpleTestCase): 
    
    # O método deve começar com 'test_'
    def test_suporte_url_exists(self): 
        try:
            url = reverse('suporte')
            self.assertIsNotNone(url) 
        except Exception as e:
            self.fail(f"NoReverseMatch para 'suporte': {e}")
