import os
import subprocess
import zipfile
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.configuracoes.models import BackupConfiguracao, HistoricoBackup

class Command(BaseCommand):
    help = 'Executa backups automáticos para todas as empresas que têm a funcionalidade ativa.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando tarefa de backups automáticos...'))
        
        # Encontra todas as configurações de backup ativas
        configs = BackupConfiguracao.objects.filter(backup_automatico=True)
        
        for config in configs:
            agora = timezone.localtime(timezone.now()).time()
            horario_backup = config.horario_backup
            
            # Verifica se está na hora de executar o backup (com uma margem de 15 minutos)
            if not (horario_backup.hour == agora.hour and horario_backup.minute <= agora.minute < horario_backup.minute + 15):
                continue # Pula se não for a hora certa

            # Verifica a frequência
            ultimo_sucesso = HistoricoBackup.objects.filter(
                empresa=config.empresa, tipo='automatico', status='sucesso'
            ).order_by('-data_criacao').first()

            if ultimo_sucesso:
                dias_desde_ultimo = (timezone.now() - ultimo_sucesso.data_criacao).days
                if config.frequencia_backup == 'diario' and dias_desde_ultimo < 1:
                    continue # Já fez backup hoje
                if config.frequencia_backup == 'semanal' and dias_desde_ultimo < 7:
                    continue # Já fez backup esta semana

            self.stdout.write(f"  -> Processando backup para: {config.empresa.nome}")
            
            # Usa a mesma lógica da view de backup manual
            backup = HistoricoBackup.objects.create(
                empresa=config.empresa,
                tipo='automatico',
                status='processando',
                solicitado_por=None # Foi automático
            )
            
            try:
                self._executar_backup_logica(backup)
                self.stdout.write(self.style.SUCCESS(f"     Backup para {config.empresa.nome} concluído com sucesso."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"     Falha no backup para {config.empresa.nome}: {e}"))
                backup.status = 'erro'
                backup.detalhes_erro = str(e)
                backup.save()

        self.stdout.write(self.style.SUCCESS('Tarefa de backups automáticos finalizada.'))
    
    def _executar_backup_logica(self, backup_obj):
        # Esta é a mesma lógica da sua view, mas adaptada para o command
        db_settings = settings.DATABASES['default']
        backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_base = f"backup_auto_{backup_obj.empresa.id}_{timestamp}"
        sql_filepath = os.path.join(backup_dir, f"{filename_base}.sql")
        zip_filepath = os.path.join(backup_dir, f"{filename_base}.zip")

        command = f"pg_dump -U {db_settings['USER']} -h {db_settings['HOST']} -p {db_settings['PORT']} {db_settings['NAME']} > {sql_filepath}"
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        process = subprocess.run(command, shell=True, env=env, capture_output=True, text=True)

        if process.returncode != 0:
            raise Exception(f"Erro no pg_dump: {process.stderr}")

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(sql_filepath, os.path.basename(sql_filepath))
        
        os.remove(sql_filepath)
        
        backup_obj.status = 'sucesso'
        backup_obj.tamanho_ficheiro = os.path.getsize(zip_filepath)
        backup_obj.ficheiro_backup.name = os.path.relpath(zip_filepath, settings.MEDIA_ROOT)
        backup_obj.save()