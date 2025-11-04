from flask import Flask, render_template, request, send_file, jsonify
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from PIL import Image
import os
from datetime import datetime

app = Flask(__name__)

# Contador simples de PDFs gerados
pdf_counter = {"total": 0, "today": 0, "users": 0}

@app.route("/")
def index():
    return render_template("index.html", count=pdf_counter["total"])

@app.route("/counter")
def counter():
    return jsonify({"count": pdf_counter["total"]})

@app.route("/upload_file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"text": ""})

    file = request.files["file"]
    filename = file.filename.lower()
    text = ""

    try:
        if filename.endswith(".pdf"):
            # Extrai texto de PDFs
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return jsonify({"text": text})
        else:
            # Para imagens: apenas gera PDF com a imagem
            img = Image.open(file)
            buffer = BytesIO()
            img.save(buffer, format="PDF")
            buffer.seek(0)

            pdf_counter["total"] += 1
            pdf_counter["today"] += 1

            return send_file(buffer, as_attachment=True, download_name="document.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"text": f"Erro ao processar arquivo: {str(e)}"})

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    text = request.form.get("text", "")
    logo_file = request.files.get("logo")
    logo_position = request.form.get("logo_position", "center")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Adiciona logo se houver
    if logo_file:
        try:
            img = Image.open(logo_file)
            img_width, img_height = img.size
            max_width = width / 3
            scale = min(max_width / img_width, 1)
            img_width *= scale
            img_height *= scale
            if logo_position == "left":
                x = 50
            elif logo_position == "center":
                x = (width - img_width) / 2
            else:  # right
                x = width - img_width - 50
            y = height - img_height - 50
            c.drawInlineImage(img, x, y, width=img_width, height=img_height)
        except:
            pass

    # Adiciona texto
    text_object = c.beginText(50, height - 150)
    text_object.setFont("Helvetica", 12)
    for line in text.split("\n"):
        text_object.textLine(line)
    c.drawText(text_object)
    c.showPage()
    c.save()
    buffer.seek(0)

    pdf_counter["total"] += 1
    pdf_counter["today"] += 1

    return send_file(buffer, as_attachment=True, download_name="document.pdf", mimetype="application/pdf")

@app.route("/admin_stats")
def admin_stats():
    return jsonify(pdf_counter)

# Rotas de páginas adicionais
@app.route("/about")
def about():
    return "<h2>About Page</h2><p>AutoPDF Cloud info...</p>"

@app.route("/privacy")
def privacy():
    return "<h2>Privacy Policy</h2><p>...</p>"

@app.route("/terms")
def terms():
    return "<h2>Terms of Service</h2><p>...</p>"

@app.route("/contact")
def contact():
    return "<h2>Contact</h2><p>...</p>"

@app.route("/faq")
def faq():
    return "<h2>FAQ</h2><p>...</p>"

@app.route("/disclaimer")
def disclaimer():
    return "<h2>Disclaimer</h2><p>...</p>"

if __name__ == "__main__":
    app.run(debug=True)
