# apps/configuracoes/services/backup_service.py
import os
import subprocess
import zipfile
from datetime import datetime, timedelta
from django.conf import settings
from apps.configuracoes.models import HistoricoBackup

def executar_backup(empresa, tipo='manual', user=None):
    """
    Executa backup completo da base de dados PostgreSQL e salva no MEDIA_ROOT/backups.
    Retorna o objeto HistoricoBackup.
    """
    db_settings = settings.DATABASES['default']
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f"backup_{empresa.id}_{timestamp}"

    sql_filepath = os.path.join(backup_dir, f"{filename_base}.sql")
    zip_filepath = os.path.join(backup_dir, f"{filename_base}.zip")

    backup_obj = HistoricoBackup.objects.create(
        empresa=empresa,
        tipo=tipo,
        status='processando',
        solicitado_por=user
    )

    try:
        # --- Executar pg_dump ---
        command = f'pg_dump -U {db_settings["USER"]} -h {db_settings["HOST"]} -p {db_settings["PORT"]} {db_settings["NAME"]} > "{sql_filepath}"'
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        process = subprocess.run(command, shell=True, env=env, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(process.stderr)

        # --- Compactar ---
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(sql_filepath, os.path.basename(sql_filepath))
        os.remove(sql_filepath)

        # --- Atualizar backup ---
        backup_obj.status = 'sucesso'
        backup_obj.tamanho_ficheiro = os.path.getsize(zip_filepath)
        backup_obj.ficheiro_backup.name = os.path.join('backups', os.path.basename(zip_filepath))
        backup_obj.save()

        return backup_obj

    except Exception as e:
        backup_obj.status = 'erro'
        backup_obj.detalhes_erro = str(e)
        backup_obj.save()
        raise e


def limpar_backups_antigos(dias=30):
    """Apaga backups mais antigos que 'dias' dias."""
    limite = datetime.now() - timedelta(days=dias)
    antigos = HistoricoBackup.objects.filter(data_criacao__lt=limite)
    for b in antigos:
        try:
            if b.ficheiro_backup and os.path.isfile(b.ficheiro_backup.path):
                os.remove(b.ficheiro_backup.path)
        except Exception:
            pass
        b.delete()
