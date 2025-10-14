# SeuApp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import Empresa
from .models import Cargo, Departamento, Funcionario # Ajuste o caminho de importação conforme sua estrutura

@receiver(post_save, sender=Funcionario)
def sincronizar_status_usuario_e_funcionario(sender, instance, **kwargs):
    """
    Sincroniza o status 'ativo' do Funcionario com o campo 'is_active' do Usuario ligado.
    Isto é CRÍTICO para segurança: garante que o acesso ao sistema é revogado se o funcionário for desativado.
    """
    
    # Verifica se há um usuário do sistema ligado a este funcionário
    if instance.usuario:
        user = instance.usuario
        
        # Regra de Segurança Crítica: Se o funcionário está inativo ou demitido
        if not instance.ativo or instance.data_demissao:
            # Desativa o acesso ao sistema (user.is_active = False)
            if user.is_active is True:
                user.is_active = False
                user.save(update_fields=['is_active'])
                # Opcional: Logar a desativação por segurança
                print(f"USUÁRIO DESATIVADO: {user.username} devido à inatividade/demissão de Funcionario.")
        
        # Regra de Reativação (se o funcionário foi reativado)
        elif instance.ativo and user.is_active is False:
             # Reativa o acesso, mas apenas se a conta não tiver sido desativada manualmente por um administrador
             # Por padrão, reativamos:
             user.is_active = True
             user.save(update_fields=['is_active'])
             print(f"USUÁRIO REATIVADO: {user.username}.")
    


# apps/funcionarios/signals.py
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .models import Empresa, Cargo, Departamento, Funcionario


# ==============================================================
# 🔹 1. CRIAÇÃO PADRÃO DE DADOS AO GERAR NOVA EMPRESA
# ==============================================================

@receiver(post_save, sender=Empresa)
def criar_padroes_empresa(sender, instance, created, **kwargs):
    """
    Ao criar uma nova empresa:
    - Replica cargos e departamentos globais.
    - Cria grupos e replica permissões dos cargos globais.
    """
    if not created:
        return

    # --- Copiar cargos globais (empresa=None) ---
    for cargo in Cargo.objects.filter(empresa__isnull=True):
        novo_cargo = Cargo.objects.create(
            nome=cargo.nome,
            codigo=f"{cargo.codigo}_{instance.id}",
            empresa=instance,
            categoria=cargo.categoria,
            nivel_hierarquico=cargo.nivel_hierarquico,
        )

        # Replica permissões padrão
        if hasattr(cargo, "permissions"):
            novo_cargo.permissions.set(cargo.permissions.all())

        # Cria grupo correspondente ao cargo
        group, _ = Group.objects.get_or_create(name=novo_cargo.nome)
        group.permissions.set(novo_cargo.permissions.all())

    # --- Copiar departamentos globais ---
    for dept in Departamento.objects.filter(loja__isnull=True):
        Departamento.objects.create(
            nome=dept.nome,
            codigo=f"{dept.codigo}_{instance.id}",
            loja=None,
            ativo=True
        )


# ==============================================================
# 🔹 2. MANTER GRUPOS SINCRONIZADOS COM CARGOS
# ==============================================================

@receiver(post_save, sender=Cargo)
def sincronizar_grupo_cargo(sender, instance, **kwargs):
    """
    Garante que o Group do Django esteja sincronizado com o Cargo:
    - Cria/atualiza o grupo.
    - Aplica as permissões do cargo no grupo.
    """
    if not instance.nome:
        return

    group, _ = Group.objects.get_or_create(name=instance.nome)
    if hasattr(instance, "permissions"):
        group.permissions.set(instance.permissions.all())


@receiver(pre_delete, sender=Cargo)
def remover_grupo_ao_excluir_cargo(sender, instance, **kwargs):
    """
    Remove automaticamente o Group ao excluir um Cargo.
    Evita deixar grupos órfãos no sistema.
    """
    try:
        Group.objects.get(name=instance.nome).delete()
    except Group.DoesNotExist:
        pass


# ==============================================================
# 🔹 3. VALIDAÇÕES E MATRÍCULA AUTOMÁTICA DE FUNCIONÁRIOS
# ==============================================================

@receiver(pre_save, sender=Funcionario)
def gerar_matricula_e_validar_funcionario(sender, instance, **kwargs):
    """Gera matrícula e valida datas importantes."""
    # Gera matrícula automática
    if not instance.matricula:
        instance.matricula = instance.gerar_matricula()

    # Valida coerência de datas
    if instance.data_demissao and instance.data_demissao <= instance.data_admissao:
        raise ValidationError("A data de demissão deve ser posterior à data de admissão.")
    if instance.data_fim_experiencia and instance.data_fim_experiencia <= instance.data_admissao:
        raise ValidationError("O fim da experiência deve ser posterior à admissão.")

    # Atualiza status de experiência
    if instance.data_fim_experiencia:
        instance.em_experiencia = instance.data_fim_experiencia > now().date()


# ==============================================================
# 🔹 4. SINCRONIZAÇÃO FUNCIONÁRIO → USUÁRIO
# ==============================================================

@receiver(post_save, sender=Funcionario)
def sincronizar_usuario_cargo(sender, instance, created, **kwargs):
    """
    Quando um funcionário é salvo:
    - Sincroniza empresa do usuário
    - Cria grupo do cargo se não existir
    - Aplica permissões do cargo no grupo
    - Garante que o usuário pertença apenas ao grupo certo
    """
    usuario = instance.usuario
    cargo = instance.cargo

    if not usuario or not cargo:
        return

    # 1️⃣ Sincroniza empresa
    if hasattr(usuario, "empresa") and usuario.empresa != instance.empresa:
        usuario.empresa = instance.empresa
        usuario.save(update_fields=["empresa"])

    # 2️⃣ Cria grupo do cargo e aplica permissões
    group, _ = Group.objects.get_or_create(name=cargo.nome)
    if hasattr(cargo, "permissions"):
        group.permissions.set(cargo.permissions.all())

    # 3️⃣ Atualiza grupos do usuário
    usuario.groups.clear()
    usuario.groups.add(group)


# ==============================================================
# 🔹 5. SINCRONIZAÇÃO REVERSA: USUÁRIO → FUNCIONÁRIO
# ==============================================================

@receiver(m2m_changed, sender=Group.user_set.through)
def sincronizar_cargo_a_partir_do_grupo(sender, instance, action, reverse, **kwargs):
    """
    Quando o grupo de um usuário é alterado (via Django Admin ou API),
    atualiza o cargo do funcionário correspondente automaticamente.
    Protege contra loops e erros de sincronização durante o salvamento.
    """
    if action not in ["post_add", "post_remove", "post_clear"]:
        return

    from .models import Funcionario, Cargo

    # Quando a mudança vem do User (não do lado reverso)
    if not reverse:
        usuario = instance
        try:
            funcionario = Funcionario.objects.get(usuario=usuario)
        except Funcionario.DoesNotExist:
            return

        # Se o funcionário ainda não tiver cargo (por salvamento em andamento), não faz nada
        if not hasattr(funcionario, "cargo_id"):
            return

        grupos = usuario.groups.all()

        if grupos.exists():
            nome_grupo = grupos.first().name
            cargo = Cargo.objects.filter(nome=nome_grupo).first()

            # Evita regravações desnecessárias e erros de integridade
            if cargo and funcionario.cargo_id != cargo.id:
                Funcionario.objects.filter(id=funcionario.id).update(cargo=cargo)
        else:
            # Remove o cargo apenas se o funcionário tiver um cargo ativo
            if funcionario.cargo_id:
                Funcionario.objects.filter(id=funcionario.id).update(cargo=None)

# ==============================================================
# 🔹 6. NOTIFICAÇÃO (OPCIONAL)
# ==============================================================

@receiver(post_save, sender=Funcionario)
def notificar_rh_novo_funcionario(sender, instance, created, **kwargs):
    """Notifica o RH sobre novos funcionários (log simples)."""
    if created:
        print(f"[INFO - RH] Novo funcionário criado: {instance.nome_completo} ({instance.matricula}) na empresa {instance.empresa.nome}")

# models.py ou signals.py
from django.contrib.auth.models import Group

def sincronizar_permissoes_cargo(funcionario):
    cargo = funcionario.cargo
    if not cargo:
        return

    # pegar ou criar o grupo
    grupo, created = Group.objects.get_or_create(name=cargo.nome)

    # limpar permissões antigas
    grupo.permissions.clear()

    # mapear campos pode_* para codenames de Permission
    permissoes_map = {
        'pode_emitir_faturacredito': 'can_emitir_faturacredito',
        'pode_liquidar_faturacredito': 'can_liquidar_faturacredito',
        # ... adicione todos os pode_* aqui
    }

    for attr, codename in permissoes_map.items():
        if getattr(cargo, attr):
            try:
                perm = Permission.objects.get(codename=codename)
                grupo.permissions.add(perm)
            except Permission.DoesNotExist:
                pass

    # associar o funcionário ao grupo
    funcionario.user.groups.clear()
    funcionario.user.groups.add(grupo)

