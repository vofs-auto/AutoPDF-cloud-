# app.py
from flask import Flask, render_template, request, send_file, jsonify
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader
from datetime import datetime
import json
import csv
from io import StringIO
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Carregar traduções
with open('translations.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

def generate_professional_pdf(text, filepath):
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-50, "AutoPDF Cloud - Documento Gerado")
    c.setFont("Helvetica", 11)
    y = height - 80
    for line in text.split('\n'):
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line[:90])
        y -= 14
    c.save()

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    return render_template('index.html', trans=translations[lang], lang=lang)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    text = request.form['text']
    filename = f"doc_{datetime.now().strftime('%H%M%S')}.pdf"
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    generate_professional_pdf(text, filepath)
    return send_file(filepath, as_attachment=True, download_name="document.pdf")

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "PDF only"}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return jsonify({"text": text[:3000]})

@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    template = request.form['template']
    csv_data = request.form['csv']
    reader = csv.DictReader(StringIO(csv_data))
    pdfs = []
    for row in reader:
        text = template
        for k, v in row.items():
            text = text.replace(f"{{{{ {k} }}}}", v)
        filename = f"pdf_{row.get('nome','doc')}.pdf"
        filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
        generate_professional_pdf(text, filepath)
        pdfs.append(filepath)
    zip_path = os.path.join(app.config['GENERATED_FOLDER'], "relatorios.zip")
    with zipfile.ZipFile(zip_path, 'w') as z:
        for p in pdfs:
            z.write(p, os.path.basename(p))
    return send_file(zip_path, as_attachment=True, download_name="relatorios.zip")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=500
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
