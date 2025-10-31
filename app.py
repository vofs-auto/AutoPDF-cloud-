from flask import Flask, render_template_string, request, send_file, jsonify
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Spacer
from PyPDF2 import PdfReader
import os
import json

app = Flask(__name__)

# --- Counter & Stats ---
pdf_counter = 0
stats = {
    "total": 0,
    "today": 0,
    "users": 0
}

# --- PDF Generation ---
def create_professional_pdf(title, content, date="", author="", watermark="AutoPDF Cloud"):
    """Generate a beautiful professional PDF with hierarchy and watermark."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Background color
    c.setFillColorRGB(0.97, 0.97, 0.97)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Frame for content
    margin = 50
    frame_width = width - 2 * margin
    frame_height = height - 2 * margin

    # --- Header Title ---
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#003366"))
    c.drawString(margin, height - 80, title[:80])

    # --- Author & Date ---
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor("#444444"))
    if author:
        c.drawString(margin, height - 100, f"Author: {author}")
    if date:
        c.drawRightString(width - margin, height - 100, f"Date: {date}")

    # --- Content Frame ---
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#222222"),
    )

    text = Paragraph(content.replace("\n", "<br/>"), body_style)
    frame = Frame(margin, margin + 60, frame_width, frame_height - 130, showBoundary=0)
    frame.addFromList([text, Spacer(1, 12)], c)

    # --- Watermark ---
    c.saveState()
    c.setFont("Helvetica-BoldOblique", 36)
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.15)  # translucent
    c.drawRightString(width - 30, 40, watermark)
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# --- Routes ---
@app.route("/")
def index():
    return render_template_string(open("templates/index.html").read(), count=pdf_counter)


@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    global pdf_counter, stats
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    pdf_counter += 1
    stats["total"] += 1
    stats["today"] += 1

    now = datetime.now().strftime("%d %B %Y")
    pdf_buffer = create_professional_pdf(
        title="Document",
        content=text,
        date=now,
        author="AutoPDF User"
    )

    return send_file(pdf_buffer, as_attachment=True, download_name="document.pdf", mimetype="application/pdf")


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"})
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return jsonify({"text": text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/generate_batch", methods=["POST"])
def generate_batch():
    global pdf_counter, stats
    data = request.get_json()
    rows = data.get("rows", [])
    if not rows:
        return jsonify({"error": "No batch data"}), 400

    merged = BytesIO()
    c = canvas.Canvas(merged, pagesize=A4)
    width, height = A4

    for row in rows:
        name = row.get("name", "")
        subject = row.get("subject", "")
        date = row.get("date", "")
        details = row.get("details", "")

        c.setFillColorRGB(0.97, 0.97, 0.97)
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # Header
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(colors.HexColor("#004488"))
        c.drawString(60, height - 80, name[:80])

        # Subtitle
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#222222"))
        c.drawString(60, height - 110, subject)

        # Date
        c.setFont("Helvetica-Oblique", 11)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawRightString(width - 60, height - 110, date)

        # Body
        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#222222"),
        )
        text = Paragraph(details.replace("\n", "<br/>"), body_style)
        frame = Frame(60, 80, width - 120, height - 220, showBoundary=0)
        frame.addFromList([text], c)

        # Watermark
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


@app.route("/counter")
def counter():
    return jsonify({"count": pdf_counter})


@app.route("/admin_stats")
def admin_stats():
    return jsonify(stats)


# --- Pages ---
@app.route("/about")
def about():
    return "<h3>About AutoPDF Cloud</h3><p>A modern PDF generator for professionals, eBooks, resumes and digital documents.</p>"

@app.route("/privacy")
def privacy():
    return "<h3>Privacy Policy</h3><p>We respect your privacy. No document data is stored on our servers.</p>"

@app.route("/terms")
def terms():
    return "<h3>Terms of Service</h3><p>Use AutoPDF Cloud responsibly for legal and creative purposes.</p>"

@app.route("/contact")
def contact():
    return "<h3>Contact</h3><p>Email: support@autopdfcloud.com</p>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
