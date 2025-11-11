document.addEventListener('DOMContentLoaded', function() {
    const selecionarTodos = document.querySelector('#id_selecionar_todos');
    if (!selecionarTodos) return;

    selecionarTodos.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (cb.id !== 'id_ativo' && cb.id !== 'id_selecionar_todos') {
                cb.checked = selecionarTodos.checked;
            }
        });
    });
});
