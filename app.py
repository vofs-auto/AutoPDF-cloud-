from flask import Flask, render_template, request, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import json, os
from datetime import datetime

app = Flask(__name__)

COUNTER_FILE = "counter.json"

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            json.dump({"count": 0}, f)
    with open(COUNTER_FILE, "r") as f:
        return json.load(f)

def save_counter(value):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": value}, f)

def increment_counter():
    data = load_counter()
    data["count"] += 1
    save_counter(data["count"])
    return data["count"]

def get_counter():
    return load_counter()["count"]

# ----- DRAW CARD FUNCTION -----
def draw_card(c, width, height, record):
    pad = 40
    c.setFillColorRGB(0.06,0.11,0.18)
    c.roundRect(pad, pad, width - 2*pad, height - 2*pad, 12, stroke=0, fill=1)
    c.setFillColorRGB(0.0,0.8,0.94)
    c.roundRect(pad, height - 80, width - 2*pad, 18, 6, stroke=0, fill=1)

    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(pad + 14, height - 100, record.get('subject','').strip()[:80])
    c.setFont("Helvetica", 13)
    c.setFillColorRGB(0.88,0.96,1)
    c.drawString(pad + 14, height - 130, "Name: " + record.get('name','').strip())
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.78,0.86,0.9)
    c.drawString(pad + 14, height - 150, "Date: " + record.get('date','').strip())

    details = record.get('details','').strip()
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.9,0.95,1)
    text = c.beginText()
    text.setTextOrigin(pad + 14, height - 180)
    text.setLeading(14)
    max_chars = 70
    for line in details.splitlines() or ['']:
        while len(line) > max_chars:
            text.textLine(line[:max_chars])
            line = line[max_chars:]
        text.textLine(line)
    c.drawText(text)

# ----- ROUTES -----
@app.route('/')
def index():
    return render_template('index.html', count=get_counter())

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    text = request.form.get('text','').replace('\r','')
    if not text:
        return "No text", 400
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "AutoPDF Cloud")
    c.setFont("Helvetica", 12)
    y -= 30
    for line in text.split('\n'):
        if y < 60:
            c.showPage()
            c.setFont("Helvetica",12)
            y = height - 60
        c.drawString(50, y, line)
        y -= 16
    c.save()
    buffer.seek(0)
    increment_counter()
    return send_file(buffer, as_attachment=True, download_name="document.pdf", mimetype='application/pdf')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error":"No file"}),400
    file = request.files['file']
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file)
        text = ""
        for p in reader.pages:
            text += (p.extract_text() or "") + "\n"
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    data = request.get_json(silent=True)
    if not data or 'rows' not in data:
        return "Bad request", 400
    rows = data['rows']
    if not isinstance(rows, list) or len(rows) == 0:
        return "No rows", 400
    if len(rows) > 82:
        return "Too many rows (max 82)", 400

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    for record in rows:
        draw_card(c, width, height, record)
        c.showPage()

    c.save()
    buffer.seek(0)
    increment_counter()
    filename = f"batch_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/counter')
def counter():
    return jsonify({"count": get_counter()})

@app.route('/about')
def about(): return render_template('about.html')
@app.route('/contact')
def contact(): return render_template('contact.html')
@app.route('/privacy')
def privacy(): return render_template('privacy.html')
@app.route('/terms')
def terms(): return render_template('terms.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
