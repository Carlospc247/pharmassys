# apps/saft/services/contabilidade_service.py
from typing import List, Dict
from apps.financeiro.models import PlanoContas, LancamentoFinanceiro # 🚨 Alterado para usar LancamentoFinanceiro
from apps.core.models import Empresa 
from datetime import datetime, date, timedelta
from decimal import Decimal

class SaftContabilidadeService:
    """
    Serviço robusto para extrair e formatar o Plano de Contas (General Ledger)
    e os Lançamentos Contábeis (GeneralLedgerEntries) para o SAF-T (AO).
    """
    
    def __init__(self, empresa: Empresa):
        self.empresa = empresa

    def get_contas_para_saft(self) -> List[Dict]:
        """
        Retorna a lista de Contas-Folha do Plano de Contas para o bloco <GeneralLedger>.
        """
        # Apenas contas da empresa, ativas e que aceitam lançamentos
        contas_folha = PlanoContas.objects.filter(
            empresa=self.empresa,
            ativa=True,
            aceita_lancamento=True 
        ).order_by('codigo')

        saft_accounts = []
        for conta in contas_folha:
            # 🚨 Lógica de Saldos Iniciais: Altamente complexa e geralmente requer 
            # o saldo do dia anterior ao período. Para produção, DEVE ser calculada
            # com base em lançamentos passados.
            
            # Placeholder: Assume 0 no início do período para a primeira iteração, 
            # mas o sistema DEVE calcular o saldo real.
            opening_balance = self._calcular_saldo_inicial(conta, date.today() - timedelta(days=365)) 

            saft_accounts.append({
                'AccountID': conta.codigo, 
                'AccountDescription': conta.nome,
                # Saldo inicial: Assume que a conta tem natureza (D/C)
                'OpeningDebitBalance': float(opening_balance) if opening_balance >= 0 else 0.00,
                'OpeningCreditBalance': float(abs(opening_balance)) if opening_balance < 0 else 0.00,
            })
            
        return saft_accounts
    
    def _calcular_saldo_inicial(self, conta: PlanoContas, data_corte: date) -> Decimal:
        """
        Método mockado. Em produção, este método deve somar todos os 
        LancamentoFinanceiro até a data de corte, respeitando D/C.
        """
        # Logica: Sum(Debitos antes da data) - Sum(Creditos antes da data)
        # Se positivo -> Débito, se negativo -> Crédito
        return Decimal('0.00') # 🚨 Implementação REAL exigida em produção

    def get_general_ledger_entries(self, data_inicio: datetime, data_fim: datetime) -> List[Dict]:
        """
        Busca os Lancamentos Contábeis para o GeneralLedgerEntries.
        Esta é a fonte de verdade do Diário Contábil.
        """
        # 1. Buscar Lançamentos dentro do período
        lancamentos = LancamentoFinanceiro.objects.filter(
            empresa=self.empresa,
            data_lancamento__range=[data_inicio.date(), data_fim.date()]
        ).select_related('plano_contas', 'origem_movimentacao') 

        saft_entries = []
        for lancamento in lancamentos:
            
            # 2. Mapeamento de Débito/Crédito
            debit = float(lancamento.valor) if lancamento.tipo == 'debito' else 0.00
            credit = float(lancamento.valor) if lancamento.tipo == 'credito' else 0.00
            
            # O campo "SourceID" pode ser o ID da fatura, recibo ou Movimentação Financeira
            source_id = lancamento.origem_movimentacao.numero_documento if lancamento.origem_movimentacao else f"UUID-{lancamento.transacao_uuid}"
            
            saft_entries.append({
                # TransactionID deve ser único e rastreável (ex: o UUID da transação)
                'TransactionID': str(lancamento.transacao_uuid), 
                'TransactionDate': lancamento.data_lancamento.isoformat(),
                'AccountID': lancamento.plano_contas.codigo,
                'Description': lancamento.descricao,
                'DebitAmount': debit,
                'CreditAmount': credit,
                'SystemEntryDate': lancamento.created_at.date().isoformat(), # Data de entrada no sistema
                'SourceID': source_id,
                'SourceType': 'LANCAMENTO', # Ou FATURA, RECIBO, etc.
            })

        return saft_entries