#apps/core/services.py
from django.db import transaction
from django.utils import timezone
from apps.core.models import ContadorDocumento # Assumindo a localização

import random
import string
from django.db import transaction
from django.utils import timezone
from apps.core.models import ContadorDocumento

def gerar_numero_documento(empresa, tipo_documento):
    """
    Gera e reserva o próximo número sequencial no formato:
    FR PMA1XYZ2025/001
    
    Onde:
        FR    -> Tipo do documento
        PMA   -> 3 iniciais da empresa
        1     -> ID da empresa
        XYZ   -> 3 letras aleatórias (A–Z)
        2025  -> Ano em curso
        /001  -> Número sequencial de 6 dígitos
    """
    ano_atual = timezone.now().year

    with transaction.atomic():
        contador, created = ContadorDocumento.objects.select_for_update().get_or_create(
            empresa=empresa,
            tipo_documento=tipo_documento,
            ano=ano_atual,
            defaults={'ultimo_numero': 0}
        )

        contador.ultimo_numero += 1
        contador.save()

        # 1️⃣ Três primeiras letras da empresa (sem espaços)
        prefixo_empresa = ''.join(empresa.nome.upper().split())[:5]

        # 2️⃣ ID da empresa
        id_empresa = str(empresa.pk)

        # 3️⃣ Sufixo aleatório (3 letras entre A–Z)
        sufixo_random = ''.join(random.choices(string.ascii_uppercase, k=3))

        # 4️⃣ Ano atual
        ano = str(ano_atual)

        # 5️⃣ Sequencial
        numero_sequencial = f"{contador.ultimo_numero:03d}"

        # 6️⃣ Montagem final
        numero_final = f"{tipo_documento} {prefixo_empresa}{id_empresa}{sufixo_random}{ano}/{numero_sequencial}"

        return numero_final
  