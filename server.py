"""
mdConvertor — server.py
Flask application exposing:
  GET  /                  → serves index.html
  POST /api/convert       → multipart file → Markdown JSON
  POST /api/convert-url   → JSON {url} → Markdown JSON
"""
import os
import sys
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template, send_from_directory
from markitdown import MarkItDown

# ── Template directory (patched by main.py before import) ────────────────────
TEMPLATE_DIR = os.environ.get(
    "MDCONVERTOR_TEMPLATE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
)

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024  # 256 MB upload limit

md = MarkItDown()

# ── Allowed extensions ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "csv", "json", "html", "htm", "xml",
    "png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff",
    "mp3", "wav", "ogg", "m4a", "flac",
    "zip", "epub",
    "txt", "md", "rst",
}


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/convert", methods=["POST"])
def convert_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not supported: {file.filename}"}), 415

    # Save upload to a temp file preserving the original extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        result = md.convert(tmp_path)
        markdown_text = result.text_content

        return jsonify({
            "markdown": markdown_text,
            "filename": file.filename,
            "chars": len(markdown_text),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.route("/api/convert-url", methods=["POST"])
def convert_url():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        result = md.convert(url)
        markdown_text = result.text_content
        return jsonify({
            "markdown": markdown_text,
            "filename": "converted.md",
            "chars": len(markdown_text),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})
