#apps/relatorios/relatorios.py
import os
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm


# Função auxiliar: Cabeçalho e Rodapé
def add_header_footer(canvas, doc):
    largura, altura = A4

    # Cabeçalho (logo + título)
    logo_path = os.path.join("static", "img", "logo.png")  # ajuste para o caminho do seu logo
    try:
        canvas.drawImage(logo_path, 1 * cm, altura - 3 * cm, width=4 * cm, height=2 * cm)
    except:
        pass  # se não achar o logo, ignora

    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(6 * cm, altura - 2 * cm, "Relatório Corporativo")

    # Rodapé
    canvas.setFont("Helvetica", 9)
    canvas.drawString(1 * cm, 1 * cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    canvas.drawRightString(largura - 1 * cm, 1 * cm, f"Página {doc.page}")



def gerar_relatorio_corporativo(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relatorio_corporativo.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=3*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    elementos = []

    # Espaçamento após o cabeçalho
    elementos.append(Spacer(1, 40))

    # Subtítulo
    elementos.append(Paragraph("Resumo Geral", styles["Heading2"]))
    elementos.append(Spacer(1, 20))

    # Tabela de exemplo
    dados = [
        ["Produto", "Quantidade", "Preço Unitário", "Total"],
        ["Arroz", "10", "1.000 Kz", "10.000 Kz"],
        ["Óleo", "5", "1.500 Kz", "7.500 Kz"],
        ["Feijão", "8", "1.200 Kz", "9.600 Kz"],
    ]

    tabela = Table(dados, colWidths=[6*cm, 3*cm, 4*cm, 4*cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#004080")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 12),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elementos.append(tabela)

    # Construir PDF
    doc.build(elementos, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    return response
