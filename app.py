from flask import Flask, render_template, request, send_file, jsonify, make_response
from io import BytesIO
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PyPDF2 import PdfReader
import os, json

app = Flask(__name__)

# Fonte universal para caracteres especiais e emojis
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

# Limite de upload: 100 MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# --- Estatísticas globais ---
pdf_counter = 0
stats = {"total": 0, "today": 0, "users": 0, "last_reset": str(date.today())}


def reset_daily_stats():
    """Zera contador diário automaticamente."""
    if stats["last_reset"] != str(date.today()):
        stats["today"] = 0
        stats["last_reset"] = str(date.today())


# --- Criação de PDF Simples ---
def create_professional_pdf(content, watermark="AutoPDF Cloud"):
    """Gera um PDF limpo, com suporte Unicode, sem metadados poluídos."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Fundo suave
    c.setFillColorRGB(0.97, 0.97, 0.97)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Estilo de corpo do texto
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#222222"),
    )

    # Proteção e formatação
    safe_content = content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    text = Paragraph(safe_content, body_style)

    frame = Frame(50, 80, width - 100, height - 150, showBoundary=0)
    frame.addFromList([text, Spacer(1, 12)], c)

    # Marca d'água discreta
    c.saveState()
    c.setFont("Helvetica-BoldOblique", 34)
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.13)
    c.drawRightString(width - 30, 40, watermark)
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# --- Página principal ---
@app.route("/")
def index():
    reset_daily_stats()

    global stats
    users_cookie = request.cookies.get("users_seen")
    if not users_cookie:
        stats["users"] += 1

    resp = make_response(render_template("index.html", count=pdf_counter))
    if not users_cookie:
        resp.set_cookie("users_seen", "1", max_age=60 * 60 * 24 * 7)
    return resp


# --- Gerar PDF simples ---
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    global pdf_counter, stats
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    reset_daily_stats()
    pdf_counter += 1
    stats["total"] += 1
    stats["today"] += 1

    pdf_buffer = create_professional_pdf(content=text)
    return send_file(pdf_buffer, as_attachment=True, download_name="document.pdf", mimetype="application/pdf")


# --- Upload de PDF e extração de texto ---
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"})
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return jsonify({"text": text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)})


# --- Geração em lote (AutoPDF) ---
@app.route("/generate_batch", methods=["POST"])
def generate_batch():
    global pdf_counter, stats
    data = request.get_json()
    rows = data.get("rows", [])
    if not rows:
        return jsonify({"error": "No batch data"}), 400

    reset_daily_stats()
    merged = BytesIO()
    c = canvas.Canvas(merged, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#222222"),
    )

    for row in rows:
        name = row.get("name", "")
        subject = row.get("subject", "")
        date_str = row.get("date", "")
        details = row.get("details", "")

        c.setFillColorRGB(0.97, 0.97, 0.97)
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # Cabeçalho
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#004488"))
        c.drawString(60, height - 80, name[:80])

        # Assunto e data
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#222222"))
        c.drawString(60, height - 110, subject)
        c.setFont("Helvetica-Oblique", 11)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawRightString(width - 60, height - 110, date_str)

        # Corpo
        safe_details = details.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        text = Paragraph(safe_details, body_style)
        frame = Frame(60, 80, width - 120, height - 220, showBoundary=0)
        frame.addFromList([text], c)

        # Marca d’água
        c.saveState()
        c.setFont("Helvetica-BoldOblique", 34)
        c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.13)
        c.drawRightString(width - 30, 40, "AutoPDF Cloud")
        c.restoreState()

        c.showPage()

    c.save()
    merged.seek(0)

    pdf_counter += len(rows)
    stats["total"] += len(rows)
    stats["today"] += len(rows)

    return send_file(merged, as_attachment=True, download_name="batch_cards.pdf", mimetype="application/pdf")


# --- Estatísticas e contadores ---
@app.route("/counter")
def counter():
    return jsonify({"count": pdf_counter})


@app.route("/admin_stats")
def admin_stats():
    reset_daily_stats()
    return jsonify(stats)


# --- Páginas HTML ---
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/cookies")
def cookies():
    return render_template("cookies.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


# --- Tema claro/escuro ---
@app.route("/set_theme/<mode>")
def set_theme(mode):
    resp = make_response(jsonify({"success": True}))
    if mode in ["light", "dark"]:
        resp.set_cookie("theme", mode, max_age=60 * 60 * 24 * 30)
    return resp


# --- Inicialização ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
