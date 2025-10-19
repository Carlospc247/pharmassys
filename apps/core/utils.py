# apps/core/utils.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import black, darkblue
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import io
import qrcode
from PIL import Image
from django.conf import settings
from django.utils import timezone
import uuid


class GeradorDocumentos:
    """Gerador de documentos PDF para vendas"""
    
    def __init__(self):
        self.width, self.height = A4
        
    def gerar_fatura(self, venda):
        """Gera fatura em PDF"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # Cabeçalho da empresa
        self._cabecalho_empresa(p, venda.empresa)
        
        # Título
        y = self.height - 5*cm
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(darkblue)
        p.drawString(2*cm, y, "FATURA")
        
        # Número da fatura
        p.setFont("Helvetica-Bold", 12)
        p.setFillColor(black)
        p.drawString(15*cm, y, f"Nº {venda.numero_venda or venda.id:06d}")
        
        # Dados do cliente
        y -= 1.5*cm
        self._dados_cliente(p, venda.cliente, y)
        
        # Dados da venda
        y -= 3*cm
        self._dados_venda(p, venda, y)
        
        # Tabela de itens
        y -= 2*cm
        y = self._tabela_itens(p, venda.itens.all(), y)
        
        # Totais
        y -= 1*cm
        self._resumo_financeiro(p, venda, y)
        
        # QR Code
        self._adicionar_qr_code(p, venda)
        
        # Rodapé
        self._rodape(p, venda)
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def gerar_recibo(self, venda):
        """Gera recibo em PDF"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # Cabeçalho
        self._cabecalho_empresa(p, venda.empresa)
        
        # Título
        y = self.height - 5*cm
        p.setFont("Helvetica-Bold", 22)
        p.setFillColor(darkblue)
        p.drawString(2*cm, y, "RECIBO")
        
        # Número
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(black)
        p.drawString(15*cm, y, f"Nº {venda.numero_venda or venda.id:06d}")
        
        # Valor em destaque
        y -= 2*cm
        total = float(venda.total or 0)
        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(darkblue)
        p.drawString(2*cm, y, f"VALOR: AKZ {total:.2f}")
        
        # Informações do recibo
        y -= 1.5*cm
        self._dados_recibo(p, venda, y)
        
        # Assinatura
        y -= 4*cm
        self._area_assinatura(p, venda, y)
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def gerar_proforma(self, venda):
        """Gera fatura proforma em PDF"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        # Marca d'água PROFORMA
        self._marca_dagua_proforma(p)
        
        # Cabeçalho
        self._cabecalho_empresa(p, venda.empresa)
        
        # Título
        y = self.height - 5*cm
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(darkblue)
        p.drawString(2*cm, y, "FATURA PROFORMA")
        
        # Aviso
        y -= 0.8*cm
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.red)
        p.drawString(2*cm, y, "* DOCUMENTO PROVISÓRIO - NÃO POSSUI VALOR FISCAL *")
        
        # Resto similar à fatura
        y -= 1*cm
        self._dados_cliente(p, venda.cliente, y)
        
        y -= 3*cm
        self._dados_venda(p, venda, y)
        
        y -= 2*cm
        y = self._tabela_itens(p, venda.itens.all(), y)
        
        y -= 1*cm
        self._resumo_financeiro(p, venda, y)
        
        # Condições
        y -= 2*cm
        self._condicoes_proforma(p, y)
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def gerar_talao_troco(self, venda):
        """Gera talão de troco"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=(8*cm, 12*cm))  # Tamanho pequeno
        
        # Título
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredText(4*cm, 10*cm, "TALÃO DE TROCO")
        
        # Dados
        p.setFont("Helvetica", 10)
        y = 9*cm
        p.drawString(0.5*cm, y, f"Venda: {venda.numero_venda or venda.id:06d}")
        y -= 0.5*cm
        p.drawString(0.5*cm, y, f"Data: {venda.data_venda.strftime('%d/%m/%Y %H:%M')}")
        y -= 0.5*cm
        p.drawString(0.5*cm, y, f"Total: AKZ {float(venda.total or 0):.2f}")
        y -= 0.5*cm
        p.drawString(0.5*cm, y, f"Troco: AKZ {float(venda.troco or 0):.2f}")
        
        # Linha para assinatura
        y -= 2*cm
        p.line(0.5*cm, y, 7.5*cm, y)
        y -= 0.3*cm
        p.setFont("Helvetica", 8)
        p.drawCentredText(4*cm, y, "Assinatura do Cliente")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
    
    def _cabecalho_empresa(self, p, empresa):
        """Adiciona cabeçalho da empresa"""
        if not empresa:
            return
            
        y = self.height - 2*cm
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(darkblue)
        p.drawString(2*cm, y, empresa.nome)
        
        y -= 0.5*cm
        p.setFont("Helvetica", 10)
        p.setFillColor(black)
        p.drawString(2*cm, y, f"NIF: {empresa.nif or 'Não informado'}")
        
        y -= 0.3*cm
        endereco = f"{empresa.endereco}, {empresa.cidade}"
        p.drawString(2*cm, y, endereco)
        
        y -= 0.3*cm
        p.drawString(2*cm, y, f"Tel: {empresa.telefone or 'Não informado'}")
    
    def _dados_cliente(self, p, cliente, y):
        """Adiciona dados do cliente"""
        p.setFont("Helvetica-Bold", 12)
        p.drawString(2*cm, y, "DADOS DO CLIENTE:")
        
        y -= 0.6*cm
        p.setFont("Helvetica", 10)
        
        if cliente:
            p.drawString(2*cm, y, f"Nome: {cliente.nome_completo}")
            y -= 0.4*cm
            if cliente.bi:
                p.drawString(2*cm, y, f"BI: {cliente.bi}")
                y -= 0.4*cm
            if cliente.telefone:
                p.drawString(2*cm, y, f"Telefone: {cliente.telefone}")
        else:
            p.drawString(2*cm, y, "Nome: Consumidor Final")
    
    def _dados_venda(self, p, venda, y):
        """Adiciona dados da venda"""
        p.setFont("Helvetica", 10)
        p.drawString(2*cm, y, f"Data: {venda.data_venda.strftime('%d/%m/%Y %H:%M')}")
        
        y -= 0.4*cm
        if venda.vendedor:
            p.drawString(2*cm, y, f"Vendedor: {venda.vendedor.get_full_name()}")
    
    def _tabela_itens(self, p, itens, y_start):
        """Cria tabela de itens"""
        # Cabeçalho da tabela
        p.setFont("Helvetica-Bold", 10)
        p.drawString(2*cm, y_start, "DESCRIÇÃO")
        p.drawString(10*cm, y_start, "QTD")
        p.drawString(12*cm, y_start, "PREÇO")
        p.drawString(15*cm, y_start, "TOTAL")
        
        # Linha
        y_start -= 0.3*cm
        p.line(2*cm, y_start, 18*cm, y_start)
        
        # Itens
        y = y_start - 0.3*cm
        p.setFont("Helvetica", 9)
        
        for item in itens:
            if y < 5*cm:  # Nova página se necessário
                p.showPage()
                y = self.height - 2*cm
            
            nome = item.produto.nome_comercial
            if len(nome) > 40:
                nome = nome[:37] + "..."
            
            p.drawString(2*cm, y, nome)
            p.drawString(10*cm, y, str(item.quantidade))
            p.drawString(12*cm, y, f"AKZ {float(item.preco_unitario):.2f}")
            p.drawString(15*cm, y, f"AKZ {float(item.total):.2f}")
            
            y -= 0.5*cm
        
        return y
    
    def _resumo_financeiro(self, p, venda, y):
        """Adiciona resumo financeiro"""
        y -= 0.5*cm
        p.line(12*cm, y, 18*cm, y)
        
        y -= 0.5*cm
        p.setFont("Helvetica", 10)
        
        subtotal = float(venda.subtotal or 0)
        desconto = float(venda.desconto_valor or 0)
        total = float(venda.total or 0)
        
        if subtotal > 0:
            p.drawString(12*cm, y, "Subtotal:")
            p.drawString(15*cm, y, f"AKZ {subtotal:.2f}")
            y -= 0.4*cm
        
        if desconto > 0:
            p.drawString(12*cm, y, "Desconto:")
            p.drawString(15*cm, y, f"AKZ {desconto:.2f}")
            y -= 0.4*cm
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(12*cm, y, "TOTAL:")
        p.drawString(15*cm, y, f"AKZ {total:.2f}")
        
        # Forma de pagamento
        if hasattr(venda, 'forma_pagamento_display'):
            y -= 0.8*cm
            p.setFont("Helvetica", 10)
            p.drawString(12*cm, y, f"Pagamento: {venda.forma_pagamento_display}")
    
    def _adicionar_qr_code(self, p, venda):
        """Adiciona QR Code ao documento"""
        try:
            # Dados para o QR Code
            qr_data = f"venda:{venda.id}:{venda.numero_venda or 'SN'}:{float(venda.total or 0):.2f}"
            
            # Gerar QR Code
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvar temporariamente
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Adicionar ao PDF
            p.drawInlineImage(qr_buffer, 15*cm, 3*cm, width=3*cm, height=3*cm)
            
            # Texto explicativo
            p.setFont("Helvetica", 8)
            p.drawCentredText(16.5*cm, 2.5*cm, "QR Code para verificação")
            
        except Exception as e:
            print(f"Erro ao gerar QR Code: {e}")
    
    def _dados_recibo(self, p, venda, y):
        """Dados específicos do recibo"""
        p.setFont("Helvetica", 11)
        
        cliente_nome = venda.cliente.nome_completo if venda.cliente else "Consumidor Final"
        p.drawString(2*cm, y, f"Recebi de: {cliente_nome}")
        
        y -= 0.6*cm
        total = float(venda.total or 0)
        p.drawString(2*cm, y, f"A quantia de: AKZ {total:.2f}")
        
        
        y -= 0.6*cm
        p.drawString(2*cm, y, f"Data: {venda.data_venda.strftime('%d/%m/%Y')}")
    
    def _area_assinatura(self, p, venda, y):
        """Área para assinatura"""
        p.setFont("Helvetica", 10)
        p.drawString(12*cm, y, f"Luanda, {venda.data_venda.strftime('%d de %B de %Y')}")
        
        y -= 1*cm
        p.line(12*cm, y, 18*cm, y)
        
        y -= 0.3*cm
        p.setFont("Helvetica-Bold", 9)
        empresa_nome = venda.empresa.nome if venda.empresa else "Farmácia"
        p.drawString(12*cm, y, empresa_nome)
        
        y -= 0.2*cm
        p.setFont("Helvetica", 8)
        p.drawString(12*cm, y, "Assinatura do Responsável")
    
    def _marca_dagua_proforma(self, p):
        """Adiciona marca d'água PROFORMA"""
        p.saveState()
        p.setFillColor(colors.lightgrey)
        p.setFont("Helvetica-Bold", 60)
        p.translate(self.width/2, self.height/2)
        p.rotate(45)
        p.drawCentredText(0, 0, "PROFORMA")
        p.restoreState()
    
    def _condicoes_proforma(self, p, y):
        """Condições da proforma"""
        p.setFont("Helvetica-Bold", 11)
        p.drawString(2*cm, y, "CONDIÇÕES:")
        
        y -= 0.6*cm
        p.setFont("Helvetica", 9)
        condicoes = [
            "• Esta proforma é válida por 30 dias",
            "• Preços sujeitos a alteração sem aviso",
            "• Sujeito à disponibilidade de stock",
            "• Documento sem valor fiscal"
        ]
        
        for condicao in condicoes:
            p.drawString(2*cm, y, condicao)
            y -= 0.4*cm
    
    def _rodape(self, p, venda):
        """Rodapé do documento"""
        p.setFont("Helvetica", 8)
        p.drawString(2*cm, 2*cm, f"Documento gerado em {timezone.now().strftime('%d/%m/%Y às %H:%M')}")
        p.drawString(2*cm, 1.5*cm, "Este documento é válido para todos os fins legais.")




import qrcode
import base64
from io import BytesIO
"""
def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao = getattr(fatura, 'data_emissao', None)
    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    numero = getattr(fatura, 'numero', getattr(fatura, 'numero_proforma', 'N/A'))
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')

    dados_qr = (
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número/Tipo: {numero} / {tipo_documento}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente}\n"
        f"Site: {site_empresa}"
    )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

"""



"""

def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao = getattr(fatura, 'data_emissao', None)
    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    numero = getattr(fatura, 'numero', getattr(fatura, 'numero_proforma', 'N/A'))
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Formatar dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente}\n"
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento, se necessário
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


"""

"""
def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente_nome = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao = getattr(fatura, 'data_emissao', None)
    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    numero = getattr(fatura, 'numero', getattr(fatura, 'numero_proforma', 'N/A'))
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Formatar dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente_nome}\n"  # Corrigido para 'cliente_nome'
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento, se necessário
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

"""
"""

def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente_nome = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao = getattr(fatura, 'data_emissao', None)
    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    numero = getattr(fatura, 'numero', getattr(fatura, 'numero_proforma', 'N/A'))
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Formatar dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente_nome}\n"
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento, se necessário
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

"""

"""
def gerar_qr_fatura(fatura, request=None):
   
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente_nome = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao = getattr(fatura, 'data_emissao', None)
    tipo_documento = getattr(fatura, 'tipo_venda', 'tipo_recibo', 'fatura_credito','Proforma')
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Determina o número de acordo com o tipo de documento
    if 'Recibo' in tipo_documento:
        numero = getattr(fatura, 'numero_recibo', 'N/A')  # Número do recibo
    elif 'Crédito' in tipo_documento:
        numero = getattr(fatura, 'numero_fatura', 'N/A')  # Número da fatura de crédito
    elif 'Proforma' in tipo_documento:
        numero = getattr(fatura, 'numero_proforma', 'N/A')  # Número da fatura proforma
    else:
        numero = getattr(fatura, 'numero', 'N/A')  # Número da fatura padrão

    # Formatar dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente_nome}\n"
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento, se necessário
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

"""


"""
import pytz

def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente_nome = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao_utc = getattr(fatura, 'data_emissao', None)
    
    # Ajustar para o fuso horário local (substitua 'Africa/Luanda' pelo fuso horário correto se necessário)
    local_tz = pytz.timezone('Africa/Luanda')  
    if data_emissao_utc:
        data_emissao = data_emissao_utc.astimezone(local_tz)  # Converte para o fuso horário local
    else:
        data_emissao = None

    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Determina o número de acordo com o tipo de documento
    if 'Recibo' in tipo_documento:
        numero = getattr(fatura, 'numero_recibo', 'N/A')
    elif 'Crédito' in tipo_documento:
        numero = getattr(fatura, 'numero_fatura', 'N/A')
    elif 'Proforma' in tipo_documento:
        numero = getattr(fatura, 'numero_proforma', 'N/A')
    else:
        numero = getattr(fatura, 'numero_venda', 'N/A')

    # Formatar dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente_nome}\n"
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento, se necessário
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

"""

import pytz
from io import BytesIO
import base64
import qrcode

def gerar_qr_fatura(fatura, request=None):
    
    usuario = getattr(request.user, 'get_full_name', lambda: None)() if request else "Sistema"
    cliente_nome = getattr(fatura.cliente, 'nome', 'Consumidor Final')
    data_emissao_utc = getattr(fatura, 'data_emissao', None)
    
    # Ajustar para o fuso horário local
    local_tz = pytz.timezone('Africa/Luanda')  
    if data_emissao_utc:
        data_emissao = data_emissao_utc.astimezone(local_tz)  # Converte para o fuso horário local
    else:
        data_emissao = None

    tipo_documento = getattr(fatura, 'tipo_venda', 'Documento')
    status = getattr(fatura, 'status', 'N/A')
    nome_empresa = getattr(fatura.empresa, 'razao_social', getattr(fatura.empresa, 'nome_fantasia', 'Empresa'))
    site_empresa = getattr(fatura.empresa, 'site', 'https://vistogest.com')
    total_fatura = getattr(fatura, 'total', 0)  # Obter total da fatura

    # Determina o número de acordo com o tipo de documento
    if 'Recibo' in tipo_documento:
        numero = getattr(fatura, 'numero_recibo', 'N/A')
    elif 'Crédito' in tipo_documento:
        numero = getattr(fatura, 'numero_fatura', 'N/A')
    elif 'Proforma' in tipo_documento:
        numero = getattr(fatura, 'numero_proforma', 'N/A')
    else:
        numero = getattr(fatura, 'numero', 'N/A')

    # Formatação dos dados do QR de acordo com o tipo de documento
    dados_qr = (
        f"Tipo de Documento: {tipo_documento}\n"
        f"Empresa: {nome_empresa}\n"
        f"Data Emissão: {data_emissao.strftime('%d/%m/%Y %H:%M') if data_emissao else 'N/A'}\n"
        f"Utilizador: {usuario}\n"
        f"Número: {numero}\n"
        f"Status: {status}\n"
        f"Cliente: {cliente_nome}\n"
        f"Total: {total_fatura:.2f} Kz\n"
        f"Site: {site_empresa}\n"
    )

    # Adicionar informações específicas para cada tipo de documento
    if 'Recibo' in tipo_documento:
        forma_pagamento = getattr(fatura, 'forma_pagamento', 'N/A')
        valor_pago = getattr(fatura, 'valor_recebido', 'N/A')  # Valor recebido no recibo
        dados_qr += f"Forma de Pagamento: {forma_pagamento}\n"
        dados_qr += f"Forma de Pagamento: {data_emissao}\n"
        dados_qr += f"Valor Pago: {valor_pago:.2f} Kz\n"

    if 'Crédito' in tipo_documento or 'Proforma' in tipo_documento:
        data_vencimento = getattr(fatura, 'data_vencimento', None)
        dados_qr += (
            f"Data Vencimento: {data_vencimento.strftime('%d/%m/%Y') if data_vencimento else 'N/A'}\n"
        )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        box_size=4,
        border=2
    )
    qr.add_data(dados_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Converter para base64 para embutir no HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"







