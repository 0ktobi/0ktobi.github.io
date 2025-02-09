import os
import random
import time  
from flask import Flask, request, render_template_string, send_file, session, jsonify
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
                return render_template_string(template, pdf_uploaded=True, filename=pdf_file.filename)
    
    return render_template_string(template, pdf_uploaded=False)

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

template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Random PDF Page Viewer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

    <script>
        $(document).ready(function() {
            if (localStorage.getItem("darkMode") === "enabled") {
                $("body").addClass("bg-dark text-white");
                $("#dark-mode-toggle").text("Light Mode");
            }

            function toggleDarkMode() {
                $("body").toggleClass("bg-dark text-white");
                if ($("body").hasClass("bg-dark")) {
                    localStorage.setItem("darkMode", "enabled");
                    $("#dark-mode-toggle").text("Light Mode");
                } else {
                    localStorage.setItem("darkMode", "disabled");
                    $("#dark-mode-toggle").text("Dark Mode");
                }
            }

            $("#dark-mode-toggle").click(toggleDarkMode);

            function updateImage(timestamp) {
                $("#pdf-image").attr("src", "/show_page?t=" + timestamp);
            }

            function getRandomPage() {
                $.post("/random_page", function(data) {
                    if (data.page_num) {
                        updateImage(data.timestamp);
                        $("#page-info").text(`Page ${data.page_num} of ${data.total_pages}`);
                        $("#prev-page-button").prop("disabled", data.page_num === 1);
                        $("#next-page-button").prop("disabled", data.page_num === data.total_pages);
                    }
                });
            }

            function navigatePage(direction) {
                $.ajax({
                    type: "POST",
                    url: "/navigate_page",
                    contentType: "application/json",
                    data: JSON.stringify({ direction: direction }),
                    success: function(data) {
                        if (data.page_num) {
                            updateImage(data.timestamp);
                            $("#page-info").text(`Page ${data.page_num} of ${data.total_pages}`);
                            $("#prev-page-button").prop("disabled", data.page_num === 1);
                            $("#next-page-button").prop("disabled", data.page_num === data.total_pages);
                        }
                    }
                });
            }

            $("#random-page-button").click(getRandomPage);
            $("#prev-page-button").click(function() { navigatePage("prev"); });
            $("#next-page-button").click(function() { navigatePage("next"); });

            $(document).keydown(function(event) {
                if (event.key === "ArrowLeft") {
                    navigatePage("prev");
                } else if (event.key === "ArrowRight") {
                    navigatePage("next");
                } else if (event.key === " " || event.key === "Enter") {
                    getRandomPage();
                } else if (event.key.toLowerCase() === "l") {
                    toggleDarkMode();
                }
            });
        });
    </script>
</head>
<body class="container mt-3">

    <div class="d-flex justify-content-between align-items-center">
        <h2 class="fs-5">Random PDF Page Viewer</h2>
        <button id="dark-mode-toggle" class="btn btn-outline-secondary btn-sm">Dark Mode</button>
    </div>

    {% if not pdf_uploaded %}
        <form method="POST" enctype="multipart/form-data" class="text-center mt-3">
            <input type="file" name="pdf_file" accept="application/pdf" class="form-control form-control-sm mb-2" required>
            <button type="submit" class="btn btn-primary btn-sm">Upload PDF</button>
        </form>
    {% else %}
        <div class="text-center mt-3">
            <h5 class="fs-6">Viewing: {{ filename }}</h5>
            <button id="random-page-button" class="btn btn-success btn-sm">Get Random Page</button>
        </div>
        
        <div class="text-center mt-3">
            <h6 id="page-info" class="fs-6">Page ? of ?</h6>
            <img id="pdf-image" src="" alt="PDF Page" class="img-fluid border shadow-lg" style="max-height: 75vh;">
        </div>

        <div class="text-center mt-2">
            <button id="prev-page-button" class="btn btn-secondary btn-sm nav-button" data-direction="prev" disabled>Previous</button>
            <button id="next-page-button" class="btn btn-secondary btn-sm nav-button" data-direction="next" disabled>Next</button>
        </div>
    {% endif %}

</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)