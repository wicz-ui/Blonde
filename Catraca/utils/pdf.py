from io import BytesIO
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from .helpers import agora_dt, status_cartao_filter


def gerar_pdf_cartao(cartao):
    largura = 242.65
    altura = 153.0
    emitido_em = agora_dt().strftime("%d/%m/%Y %H:%M")
    codigo = str(cartao["codigo_publico"])
    qr_valor = f"CARD:{codigo}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(largura, altura))

    pdf.setFillColor(colors.HexColor("#f4f7f5"))
    pdf.roundRect(0, 0, largura, altura, 10, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.roundRect(7, 7, largura - 14, altura - 14, 9, stroke=0, fill=1)

    pdf.setFillColor(colors.HexColor("#0f766e"))
    pdf.roundRect(7, altura - 40, largura - 14, 33, 9, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(18, altura - 22, "CATRACA VIRTUAL")
    pdf.setFont("Helvetica", 6.8)
    pdf.drawString(18, altura - 33, "Cartão do Passageiro")

    pdf.setFillColor(colors.HexColor("#18241f"))
    pdf.setFont("Helvetica-Bold", 12)
    nome = str(cartao["nome_usuario"])[:26]
    pdf.drawString(18, 96, nome)

    pdf.setFont("Helvetica", 6.5)
    pdf.setFillColor(colors.HexColor("#61736b"))
    pdf.drawString(18, 82, "CÓDIGO PÚBLICO")
    pdf.setFillColor(colors.HexColor("#10231c"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(18, 58, codigo)

    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(colors.HexColor("#18241f"))
    pdf.drawString(18, 44, f"Status: {status_cartao_filter(cartao['status'])}")
    pdf.setFont("Helvetica", 5.8)
    pdf.setFillColor(colors.HexColor("#61736b"))
    pdf.drawString(18, 32, "Simulação acadêmica - sem validade para transporte.")
    pdf.setFont("Helvetica", 5.8)
    pdf.drawString(18, 17, f"Emitido em {emitido_em}")

    qr_size = 82
    qr = QrCodeWidget(qr_valor)
    bounds = qr.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0],
    )
    drawing.add(qr)
    renderPDF.draw(drawing, pdf, largura - qr_size - 15, 29)

    pdf.setFillColor(colors.HexColor("#0f766e"))
    pdf.setFont("Helvetica-Bold", 6.2)
    pdf.drawCentredString(largura - 56, 18, qr_valor)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
