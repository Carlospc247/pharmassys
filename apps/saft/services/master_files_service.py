# apps/saft/services/master_files_service.py

from typing import List, Dict, Any
from apps.core.models import Empresa 



class SaftMasterFilesService:
    """
    Serviço dedicado à extração de dados mestres (clientes, fornecedores, produtos, impostos) 
    para o bloco <MasterFiles> do SAF-T.
    """
    
    def __init__(self, empresa: Empresa):
        self.empresa = empresa

    def get_customers(self) -> List[Dict]:
        """
        Extrai e formata a lista de clientes.
        Requer campos cruciais: CustomerID, AccountID (Contabilidade), CompanyName, TaxRegistrationNumber.
        """
        # 🚨 Implementação de Produção:
        # clientes = Cliente.objects.filter(empresa=self.empresa, ativo=True)
        # return [
        #     {
        #         'CustomerID': c.codigo_cliente,
        #         'AccountID': c.plano_contas_receber.codigo, # Deve ser ligado a uma conta do Ativo/Passivo
        #         'CustomerTaxID': c.nif, 
        #         # ... mais mapeamentos SAF-T
        #     } for c in clientes
        # ]
        
        # Placeholder Mínimo Funcional:
        print("MasterFilesService: Clientes extraídos.")
        return [] 

    def get_suppliers(self) -> List[Dict]:
        
        # 🚨 Implementação de Produção:
        # fornecedores = Fornecedor.objects.filter(empresa=self.empresa, ativo=True)
        # return [
        #     {
        #         'SupplierID': f.codigo_fornecedor,
        #         'AccountID': f.plano_contas_pagar.codigo, # Deve ser ligado a uma conta do Ativo/Passivo
        #         # ... mais mapeamentos SAF-T
        #     } for f in fornecedores
        # ]

        # Placeholder Mínimo Funcional:
        print("MasterFilesService: Fornecedores extraídos.")
        return []

    def get_products(self) -> List[Dict]:
        """
        Extrai e formata a lista de produtos/serviços.
        Requer campos cruciais: ProductType (P ou S), ProductCode, ProductDescription, ProductGroup.
        """
        # 🚨 Implementação de Produção:
        # produtos = Produto.objects.filter(empresa=self.empresa, ativo=True)
        # return [
        #     {
        #         'ProductType': 'P' if p.is_stock else 'S',
        #         'ProductCode': p.sku,
        #         # ... mais mapeamentos SAF-T
        #     } for p in produtos
        # ]

        # Placeholder Mínimo Funcional:
        print("MasterFilesService: Produtos extraídos.")
        return []