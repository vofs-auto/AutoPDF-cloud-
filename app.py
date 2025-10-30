from flask import Flask, render_template, request, send_file, jsonify
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader
from datetime import datetime
import json
import csv
from io import StringIO, BytesIO
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Carregar traduções
with open('translations.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

# ---------- Função para gerar PDF ----------
def generate_professional_pdf(text, filepath):
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "AutoPDF Cloud - Documento Gerado")
    c.setFont("Helvetica", 11)

    y = height - 80
    for line in text.splitlines():  # Evita quadrados nas quebras
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60
        c.drawString(50, y, line)
        y -= 14
    c.save()

# ---------- Página inicial ----------
@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    return render_template('index.html', trans=translations[lang], lang=lang)

# ---------- Gerar PDF único ----------
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    filename = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    generate_professional_pdf(text, filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)

# ---------- Upload e leitura de PDF ----------
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be PDF"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return jsonify({"text": text[:5000]})

# ---------- Batch PDF Bot ----------
@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    template = request.form.get('template', '')
    csv_data = request.form.get('csv', '')
    if not template or not csv_data:
        return jsonify({"error": "Missing data"}), 400

    reader = csv.DictReader(StringIO(csv_data))
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for row in reader:
            text = template
            for k, v in row.items():
                text = text.replace(f"{{{{ {k} }}}}", v)
            filename = f"report_{row.get('nome', 'user')}_{datetime.now().strftime('%H%M%S')}.pdf"
            pdf_buffer = BytesIO()
            generate_professional_pdf(text, pdf_buffer)
            z.writestr(filename, pdf_buffer.getvalue())
    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name="reports.zip", mimetype='application/zip')

# ---------- Páginas estáticas ----------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

# ---------- Inicialização ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
