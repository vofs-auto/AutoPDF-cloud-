from flask import Flask, render_template, request, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black
from io import BytesIO
from datetime import datetime
import json

app = Flask(__name__)

# Counter variable (in-memory)
pdf_counter = 0

@app.route("/")
def index():
    return render_template("index.html", count=pdf_counter)

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    global pdf_counter
    text = request.form.get("text", "").strip()
    if not text:
        return "No text provided", 400

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Create blue gradient background
    for i in range(100):
        shade = 1 - (i / 120.0)
        c.setFillColorRGB(0.8 - (i/300.0), 0.9 - (i/250.0), 1)
        c.rect(0, (A4[1]/100)*i, A4[0], A4[1]/100, fill=1, stroke=0)

    c.setFillColor(black)
    c.setFont("Helvetica", 12)
    text_obj = c.beginText(50, 800)
    for line in text.splitlines():
        text_obj.textLine(line)
    c.drawText(text_obj)

    # Add watermark
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawRightString(A4[0] - 20, 20, "AutoPDF Cloud – https://autopdf-cloud-awgq.onrender.com")

    c.showPage()
    c.save()

    buffer.seek(0)
    pdf_counter += 1
    return send_file(buffer, as_attachment=True, download_name="AutoPDF.pdf", mimetype="application/pdf")

@app.route("/generate_batch", methods=["POST"])
def generate_batch():
    global pdf_counter
    data = request.get_json()
    rows = data.get("rows", [])
    if not rows:
        return "No data received", 400

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for row in rows:
        # Blue gradient background
        for i in range(100):
            shade = 1 - (i / 120.0)
            c.setFillColorRGB(0.8 - (i/300.0), 0.9 - (i/250.0), 1)
            c.rect(0, (A4[1]/100)*i, A4[0], A4[1]/100, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(black)
        c.drawCentredString(A4[0]/2, 780, "AutoPDF Cloud Report")

        c.setFont("Helvetica", 12)
        y = 740
        fields = [
            ("Name / Product", row.get("name", "")),
            ("Title / Subject", row.get("subject", "")),
            ("Date", row.get("date", "")),
            ("Details", row.get("details", "")),
        ]
        for label, value in fields:
            c.drawString(80, y, f"{label}:")
            c.drawString(220, y, value)
            y -= 24

        # Watermark
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawRightString(A4[0] - 20, 20, "AutoPDF Cloud – https://autopdf-cloud-awgq.onrender.com")

        c.showPage()

    c.save()
    buffer.seek(0)
    pdf_counter += len(rows)
    return send_file(buffer, as_attachment=True, download_name="Batch_AutoPDF.pdf", mimetype="application/pdf")

@app.route("/counter")
def counter():
    return jsonify({"count": pdf_counter})

@app.route("/admin_stats")
def admin_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    return jsonify({
        "total": pdf_counter,
        "today": today,
        "users": "Active visitors mode"
    })

# Static pages
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

if __name__ == "__main__":
    app.run(debug=True)
