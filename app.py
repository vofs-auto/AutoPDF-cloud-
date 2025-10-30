from flask import Flask, render_template, request, send_file, jsonify
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from PyPDF2 import PdfReader
from io import BytesIO
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Simple global counter (in-memory)
pdf_counter = {"count": 0}

# Helper function: create a clean professional PDF
def generate_card_pdf(cards, filepath):
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0.9, 1)
    c.drawString(margin, y, "AutoPDF Cloud - Batch PDF Cards")
    y -= 30
    c.setStrokeColorRGB(0, 1, 1)
    c.line(margin, y, width - margin, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for i, card in enumerate(cards, start=1):
        if y < 100:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 11)

        c.setFillColorRGB(0.8, 1, 1)
        c.rect(margin - 10, y - 65, width - 2 * margin + 20, 80, stroke=1, fill=0)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(margin, y, f"{i}. Name / Product: {card.get('name', '')}")
        y -= 15
        c.drawString(margin, y, f"Title / Subject: {card.get('subject', '')}")
        y -= 15
        c.drawString(margin, y, f"Date: {card.get('date', '')}")
        y -= 15
        c.drawString(margin, y, f"Details: {card.get('details', '')[:120]}")
        y -= 30

    c.showPage()
    c.save()


@app.route('/')
def index():
    return render_template('index.html', count=pdf_counter["count"])


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    text = request.form['text']
    filename = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0.9, 1)
    c.drawString(50, height - 50, "AutoPDF Cloud - Generated Document")
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(1, 1, 1)
    for line in text.split('\n'):
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line[:90])
        y -= 15
    c.save()
    pdf_counter["count"] += 1
    return send_file(filepath, as_attachment=True, download_name="document.pdf")


@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "PDF files only"}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return jsonify({"text": text[:4000]})


@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    data = request.get_json()
    cards = data.get("rows", [])
    if not cards:
        return jsonify({"error": "No cards provided"}), 400

    filename = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    generate_card_pdf(cards, filepath)
    pdf_counter["count"] += len(cards)
    return send_file(filepath, as_attachment=True, download_name="batch_cards.pdf")


@app.route('/counter')
def counter():
    return jsonify(pdf_counter)


@app.route('/admin_stats')
def admin_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    return jsonify({
        "total": pdf_counter["count"],
        "today": today,
        "users": "Active users: N/A"
    })


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
