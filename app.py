# app.py
import os
import io
import json
import re
from datetime import date
from flask import Flask, request, send_file, jsonify, render_template, abort
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import pytesseract

app = Flask(__name__, template_folder="templates", static_folder="static")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(APP_DIR, "fonts")
COUNTER_FILE = os.path.join(APP_DIR, "pdf_counter.json")

# --- Registrar fonte ---
def register_font():
    font_name = "DejaVuSans"
    possible = [
        os.path.join(FONTS_DIR, "DejaVuSans.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/DejaVuSans.ttf",
    ]
    for p in possible:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont(font_name, p))
            print(f"✅ Fonte registrada: {p}")
            return font_name
    print("⚠️ DejaVuSans.ttf não encontrado, usando Helvetica (limitado).")
    return "Helvetica"

MAIN_FONT = register_font()

# --- Funções utilitárias ---
def sanitize_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[\U00010000-\U0010FFFF]", "", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        data = {"total": 0, "today_date": date.today().isoformat(), "today": 0, "users": []}
        save_counter(data)
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_counter(data):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def increment_counter(ip):
    data = load_counter()
    today = date.today().isoformat()
    if data["today_date"] != today:
        data["today_date"] = today
        data["today"] = 0
    data["total"] += 1
    data["today"] += 1
    if ip not in data["users"]:
        data["users"].append(ip)
    save_counter(data)

# --- Rodapé discreto ---
def add_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont(MAIN_FONT, 8)
    canvas_obj.setFillGray(0.5, 0.3)
    footer_text = "AutoPDF Cloud — Professional PDF Export"
    canvas_obj.drawRightString(A4[0] - 20*mm, 10*mm, footer_text)
    canvas_obj.restoreState()

# --- Gerador de PDF com imagem opcional ---
def build_pdf(text, logo_file=None, logo_position="left"):
    buffer = io.BytesIO()
    text = sanitize_text(text)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25*mm,
        rightMargin=25*mm,
        topMargin=25*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    normal = ParagraphStyle("Normal", fontName=MAIN_FONT, fontSize=12, leading=15)
    label = ParagraphStyle("Label", fontName=MAIN_FONT, fontSize=13, leading=17, spaceAfter=6, alignment=TA_LEFT)
    title_card = ParagraphStyle("TitleCard", fontName=MAIN_FONT, fontSize=15, leading=20, spaceBefore=15, spaceAfter=10, alignment=TA_LEFT)

    story = []

    # --- Inserir logo se fornecido ---
    if logo_file:
        img_reader = ImageReader(logo_file)
        # Posição fixa
        x = {"left": 25*mm, "center": (A4[0]-50)/2, "right": A4[0]-25*mm-50}.get(logo_position, 25*mm)
        y = A4[1] - 60  # distância do topo
        def draw_logo(canvas_obj, doc_obj):
            canvas_obj.drawImage(img_reader, x, y, width=50, height=50, preserveAspectRatio=True)
            add_footer(canvas_obj, doc_obj)
        on_first = draw_logo
    else:
        on_first = add_footer

    # --- Adicionar conteúdo do texto ---
    cards = re.findall(r"Name:\s*(.*?)\nTitle:\s*(.*?)\nDate:\s*(.*?)\nDetails:\s*([\s\S]*?)(?=\nName:|\Z)", text)
    if cards:
        for i, (name, title_, date_, details) in enumerate(cards, start=1):
            story.append(Paragraph(f"Card {i}", title_card))
            story.append(Paragraph(f"<b>Name:</b> {name}", label))
            story.append(Paragraph(f"<b>Title:</b> {title_}", label))
            story.append(Paragraph(f"<b>Date:</b> {date_}", label))
            story.append(Paragraph("<b>Details:</b>", label))
            story.append(Paragraph(details.replace("\n", "<br/>"), normal))
            story.append(Spacer(1, 20))
    else:
        for para in text.split("\n\n"):
            story.append(Paragraph(para.strip().replace("\n", "<br/>"), normal))
            story.append(Spacer(1, 10))

    doc.build(story, onFirstPage=on_first, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

# --- Rotas principais ---
@app.route("/")
def index():
    data = load_counter()
    return render_template("index.html", count=data.get("total", 0))

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    text = sanitize_text(request.form.get("text", ""))
    if not text.strip():
        return jsonify({"error": "Empty text"}), 400
    logo_file = request.files.get("logo")
    logo_position = request.form.get("logo_position", "left")
    pdf_buffer = build_pdf(text, logo_file, logo_position)
    increment_counter(request.remote_addr or "anon")
    return send_file(pdf_buffer, as_attachment=True, download_name="document.pdf", mimetype="application/pdf")

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    filename = file.filename.lower()
    text = ""
    try:
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            img = Image.open(file)
            text = pytesseract.image_to_string(img)
        else:
            return jsonify({"error": "Formato não suportado"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"text": sanitize_text(text)})

@app.route("/counter")
def counter():
    return jsonify({"count": load_counter().get("total", 0)})

@app.route("/admin_stats")
def admin_stats():
    data = load_counter()
    return jsonify({"total": data["total"], "today": data["today"], "users": len(data["users"])})

# --- Páginas estáticas ---
@app.route("/about")
@app.route("/privacy")
@app.route("/terms")
@app.route("/cookies")
@app.route("/contact")
@app.route("/faq")
@app.route("/disclaimer")
def render_static_pages():
    page = request.path.strip("/")
    try:
        return render_template(f"{page}.html")
    except:
        abort(404)

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    os.makedirs(FONTS_DIR, exist_ok=True)
    load_counter()
    app.run(host="0.0.0.0", port=5000, debug=False)
