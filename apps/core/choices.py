# core/choices.py
FORMA_PAGAMENTO_CHOICES = [
    ('dinheiro', 'Dinheiro'),
    ('kwik', 'KWIK'),
    ('cartao_debito', 'Cartão de Débito'),
    ('cartao_credito', 'Cartão de Crédito'),
    ('transferencia', 'Transferência'),
    ('cheque', 'Cheque'),
    ('vale', 'Vale'),
    ('outros', 'Outros'),
]

# apps/core/choices.py

TIPO_RETENCAO_CHOICES = [
    ('IRT', 'Imposto sobre Rendimentos do Trabalho'),
    ('IRPC', 'Imposto sobre Rendimentos de Pessoas Coletivas'),
    ('IVA', 'IVA Retido na Fonte'),
    ('IS', 'Imposto do Selo'),
    ('OUTROS', 'Outros tipos de retenção'),
]
