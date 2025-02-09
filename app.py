import os
import random
import time
from flask import Flask, request, render_template, send_file, session, jsonify
import PyPDF2
from pdf2image import convert_from_path
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_random_page(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)
        random_page = random.randint(1, total_pages)
        return random_page, total_pages

def pdf_page_to_image(pdf_path, page_num):
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    img = images[0]
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "pdf_file" in request.files:
            pdf_file = request.files["pdf_file"]
            if pdf_file.filename.endswith(".pdf"):
                filepath = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
                pdf_file.save(filepath)
                session["pdf_path"] = filepath
                session.pop("random_page", None)
                return render_template("index.html", pdf_uploaded=True, filename=pdf_file.filename)
    return render_template("index.html", pdf_uploaded=False)

@app.route("/random_page", methods=["POST"])
def random_page():
    if "pdf_path" in session:
        pdf_path = session["pdf_path"]
        page_num, total_pages = get_random_page(pdf_path)
        session["random_page"] = page_num
        session["total_pages"] = total_pages
        return jsonify({"page_num": page_num, "total_pages": total_pages, "timestamp": time.time()})
    return jsonify({"error": "No PDF uploaded"}), 400

@app.route("/navigate_page", methods=["POST"])
def navigate_page():
    direction = request.json.get("direction")
    if "random_page" in session and "total_pages" in session:
        current_page = session["random_page"]
        total_pages = session["total_pages"]

        if direction == "next" and current_page < total_pages:
            session["random_page"] += 1
        elif direction == "prev" and current_page > 1:
            session["random_page"] -= 1

        return jsonify({"page_num": session["random_page"], "total_pages": total_pages, "timestamp": time.time()})
    return jsonify({"error": "No PDF uploaded"}), 400

@app.route("/show_page")
def show_page():
    if "pdf_path" in session and "random_page" in session:
        pdf_path = session["pdf_path"]
        page_num = session["random_page"]
        img_bytes = pdf_page_to_image(pdf_path, page_num)
        return send_file(img_bytes, mimetype="image/png")
    return "Error: No PDF file uploaded or page not selected.", 400

if __name__ == "__main__":
    app.run(debug=True)