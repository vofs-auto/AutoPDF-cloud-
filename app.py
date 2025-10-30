from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import json
import datetime

app = Flask(__name__)

# === Home Page ===
@app.route('/')
def index():
    return render_template('index.html')

# === Generate Batch PDF Bot ===
@app.route('/generate_batch_pdf', methods=['POST'])
def generate_batch_pdf():
    try:
        data = request.json
        entries = data.get('entries', [])

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 4 * cm  # start position

        # Page background
        def draw_background():
            c.setFillColorRGB(0.965, 0.965, 0.965)  # light gray background
            c.rect(0, 0, width, height, fill=True, stroke=False)

        draw_background()

        for entry in entries:
            name = entry.get('name', '')
            subject = entry.get('subject', '')
            date = entry.get('date', '')
            details = entry.get('details', '')

            # Draw Card Background
            card_height = 5 * cm
            c.setFillColor(colors.white)
            c.roundRect(2 * cm, y - card_height, width - 4 * cm, card_height, 10, stroke=0, fill=1)

            # Card Shadow (subtle)
            c.setFillColorRGB(0.7, 0.7, 0.7, alpha=0.2)
            c.roundRect(2.1 * cm, y - card_height - 0.1 * cm, width - 4.2 * cm, card_height, 10, stroke=0, fill=1)

            # Card Content
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2.5 * cm, y - 1 * cm, f"Name/Product: {name}")
            c.setFont("Helvetica", 11)
            c.drawString(2.5 * cm, y - 1.6 * cm, f"Subject: {subject}")
            c.drawString(2.5 * cm, y - 2.2 * cm, f"Date: {date}")
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(2.5 * cm, y - 2.8 * cm, f"Details: {details}")

            # Update Y position
            y -= card_height + 1.5 * cm

            # Add new page if needed
            if y < 6 * cm:
                # Watermark before page break
                c.setFont("Helvetica-Oblique", 9)
                c.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.4)
                c.drawRightString(width - 1.5 * cm, 1.5 * cm, "AutoPDF Cloud")
                c.showPage()
                draw_background()
                y = height - 4 * cm

        # Add watermark at bottom right of last page
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.4)
        c.drawRightString(width - 1.5 * cm, 1.5 * cm, "AutoPDF Cloud")

        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Batch_AutoPDF_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# === Single PDF Generation (normal) ===
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        text = request.form.get('text', '')
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Background
        c.setFillColorRGB(0.965, 0.965, 0.965)
        c.rect(0, 0, width, height, fill=True, stroke=False)

        c.setFont("Helvetica", 12)
        text_object = c.beginText(2.5 * cm, height - 3 * cm)
        for line in text.splitlines():
            text_object.textLine(line)
        c.drawText(text_object)

        # Watermark bottom right
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.4)
        c.drawRightString(width - 1.5 * cm, 1.5 * cm, "AutoPDF Cloud")

        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"AutoPDF_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
