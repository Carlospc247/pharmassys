# apps/servicos/management/commands/processar_notificacoes.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.servicos.models import (
    AgendamentoServico, NotificacaoAgendamento, ConfiguracaoNotificacao
)

class Command(BaseCommand):
    help = 'Processa notificações de agendamento pendentes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--criar-notificacoes',
            action='store_true',
            help='Criar notificações para agendamentos futuros'
        )
        
        parser.add_argument(
            '--enviar-pendentes',
            action='store_true',
            help='Enviar notificações pendentes'
        )
    
    def handle(self, *args, **options):
        if options['criar_notificacoes']:
            self.criar_notificacoes()
        
        if options['enviar_pendentes']:
            self.enviar_notificacoes_pendentes()
    
    def criar_notificacoes(self):
        """Cria notificações para agendamentos futuros"""
        self.stdout.write('Criando notificações para agendamentos...')
        
        # Buscar configurações de todas as empresas
        configuracoes = ConfiguracaoNotificacao.objects.all()
        
        for config in configuracoes:
            dias_notificacao = config.get_dias_notificacao_lista()
            
            # Buscar agendamentos futuros desta empresa
            agendamentos = AgendamentoServico.objects.filter(
                empresa=config.empresa,
                status='agendado',
                data_hora__gt=timezone.now()
            )
            
            for agendamento in agendamentos:
                for dias in dias_notificacao:
                    data_envio = agendamento.data_hora.date() - timedelta(days=dias)
                    
                    # Só criar se a data de envio é hoje ou no futuro
                    if data_envio >= date.today():
                        # Verificar se já existe notificação
                        existe = NotificacaoAgendamento.objects.filter(
                            agendamento=agendamento,
                            dias_antecedencia=dias
                        ).exists()
                        
                        if not existe:
                            # Criar notificações para cada canal ativo
                            if config.email_ativo:
                                self.criar_notificacao_individual(
                                    agendamento, config, dias, 'email', data_envio
                                )
                            
                            if config.sms_ativo:
                                self.criar_notificacao_individual(
                                    agendamento, config, dias, 'sms', data_envio
                                )
                            
                            if config.whatsapp_ativo:
                                self.criar_notificacao_individual(
                                    agendamento, config, dias, 'whatsapp', data_envio
                                )
        
        self.stdout.write(self.style.SUCCESS('Notificações criadas com sucesso!'))
    
    def criar_notificacao_individual(self, agendamento, config, dias, tipo, data_envio):
        """Cria uma notificação individual"""
        # Preparar dados para template
        dados = {
            'nome_paciente': agendamento.paciente_temp.cliente.nome,
            'data_consulta': agendamento.data_hora.strftime('%d/%m/%Y'),
            'hora_consulta': agendamento.data_hora.strftime('%H:%M'),
            'farmaceutico': agendamento.farmaceutico.nome,
            'servico': agendamento.servico.nome,
            'nome_empresa': config.empresa.nome,
        }
        
        # Definir título e mensagem baseado no tipo
        if tipo == 'email':
            titulo = config.template_email_titulo.format(**dados)
            mensagem = config.template_email_mensagem.format(**dados)
        else:
            titulo = f"Lembrete de Consulta - {dados['nome_paciente']}"
            mensagem = config.template_sms_mensagem.format(**dados)
        
        # Definir data e hora de envio
        hora_envio = config.horario_inicio_envio
        data_hora_envio = timezone.make_aware(
            timezone.datetime.combine(data_envio, hora_envio)
        )
        
        NotificacaoAgendamento.objects.create(
            agendamento=agendamento,
            paciente=agendamento.paciente_temp,
            tipo_notificacao=tipo,
            dias_antecedencia=dias,
            titulo=titulo,
            mensagem=mensagem,
            data_agendada_envio=data_hora_envio,
            empresa=config.empresa
        )
    
    def enviar_notificacoes_pendentes(self):
        """Envia notificações pendentes"""
        self.stdout.write('Enviando notificações pendentes...')
        
        agora = timezone.now()
        notificacoes_pendentes = NotificacaoAgendamento.objects.filter(
            status='pendente',
            data_agendada_envio__lte=agora
        )
        
        enviadas = 0
        erros = 0
        
        for notificacao in notificacoes_pendentes:
            if notificacao.enviar_notificacao():
                enviadas += 1
                self.stdout.write(f'✓ Enviada: {notificacao.paciente.cliente.nome}')
            else:
                erros += 1
                self.stdout.write(f'✗ Erro: {notificacao.paciente.cliente.nome}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processamento concluído! {enviadas} enviadas, {erros} com erro.'
            )
        )



