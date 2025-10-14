from django.db import transaction
from django.utils import timezone
from apps.core.models import ContadorDocumento # Assumindo a localização

def gerar_numero_documento(empresa, tipo_documento):
    """
    Gera e reserva o próximo número sequencial para um tipo de documento.
    
    Args:
        empresa (Empresa): A instância da empresa que emite o documento.
        tipo_documento (str): O prefixo do documento ('FR', 'FT', 'REC', 'PP').
        
    Returns:
        str: O número formatado do documento (ex: FR EMP001/001/2025).
    """
    ano_atual = timezone.now().year
    
    # Usa transaction.atomic para garantir que a atualização e leitura sejam atômicas
    with transaction.atomic():
        # Obtém ou Cria o contador. Usa select_for_update() para bloquear o registro.
        contador, created = ContadorDocumento.objects.select_for_update().get_or_create(
            empresa=empresa,
            tipo_documento=tipo_documento,
            ano=ano_atual,
            defaults={'ultimo_numero': 0}
        )
        
        # 1. Incrementa o contador
        contador.ultimo_numero += 1
        contador.save()
        
        # 2. Formata o número (Lógica de Numeração Centralizada)
        
        # Adaptação para usar parte do nome da empresa para identificação interna, se necessário.
        identificador_empresa = (empresa.nome[:4].upper().replace(" ", "") + str(empresa.pk))
        
        # Formato: PREFIXO IDENTIFICADOR/SEQUENCIAL/ANO
        # Exemplo: FR EMPR1/001/2025
        numero_sequencial = f"{contador.ultimo_numero:03d}" # 001, 002, 003...
        
        numero_final = f"{tipo_documento} {identificador_empresa}/{numero_sequencial}/{ano_atual}"
        
        return numero_final
    
    