from flask import Flask, render_template, request, send_file, jsonify, make_response
from io import BytesIO
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader
import os, json

# ✅ Registrar a fonte DejaVuSans (ótima para documentos, estudos e uso profissional)
font_path = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
else:
    print("⚠️ Fonte DejaVuSans.ttf não encontrada — usando padrão.")

app = Flask(__name__)

# Função auxiliar para gerar PDF
def generate_pdf(data_list):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # Estilo base
    text_style = ParagraphStyle(
        'Custom',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=11,
        leading=15,
        spaceAfter=8,
        textColor=colors.black
    )

    for i, item in enumerate(data_list):
        # Adiciona uma nova página se não for a primeira
        if i > 0:
            c.showPage()
        
        # Cabeçalho simples
        c.setFont("DejaVuSans", 14)
        c.drawString(60, height - 80, f"📄 Document {i+1}")
        c.line(60, height - 85, width - 60, height - 85)

        # Conteúdo principal
        y = height - 120
        for key, value in item.items():
            if isinstance(value, str):
                text = f"<b>{key.capitalize()}:</b> {value}"
                para = Paragraph(text, text_style)
                w, h = para.wrap(width - 120, height)
                if y - h < 60:
                    c.showPage()
                    y = height - 80
                para.drawOn(c, 60, y - h)
                y -= h + 8

    c.save()
    buffer.seek(0)
    return buffer

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para gerar PDF simples
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400

        buffer = generate_pdf([data])
        return send_file(
            buffer,
            as_attachment=True,
            download_name="generated.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para gerar PDFs em lote (AutoPDF)
@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    try:
        data_list = request.json
        if not data_list or not isinstance(data_list, list):
            return jsonify({"error": "Invalid data format"}), 400

        buffer = generate_pdf(data_list)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="batch_generated.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota de upload e leitura de PDF
@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        return jsonify({"content": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
