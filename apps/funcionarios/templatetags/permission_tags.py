from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def pode_acao(context, acao):
    """
    Verifica se o funcionário logado (do request) pode realizar uma ação.
    Uso: {% if pode_acao 'cadastrar_produto' %}...{% endif %}
    """
    request = context['request']
    if not request.user.is_authenticated:
        return False
        
    try:
        # Chama o seu método dinâmico
        return request.user.funcionario.pode_realizar_acao(acao)
    except AttributeError:
        # Se request.user.funcionario não existir ou a permissão falhar
        return False