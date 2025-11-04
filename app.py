from flask import Flask, render_template, request, send_file, jsonify
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/data/data/com.termux/files/usr/bin/tesseract"
# teste com qualquer imagem .png/.jpg que você tenha
text = pytesseract.image_to_string("teste.png")
print(text)
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


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"text": ""})
    
    file = request.files["file"]
    text = ""
    filename = file.filename.lower()

    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        else:
            # Para imagens: OCR
            img = Image.open(file)
            text = pytesseract.image_to_string(img)
    except Exception as e:
        return jsonify({"text": f"Error reading file: {str(e)}"})

    return jsonify({"text": text})


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
            # Reduz tamanho se necessário
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
