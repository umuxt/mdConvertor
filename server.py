"""
mdConvertor — server.py
Flask application exposing:
  GET  /                     → serves index.html
  POST /api/convert          → multipart file → Markdown JSON
  POST /api/convert-url      → JSON {url} → Markdown JSON (with YouTube support)
  POST /api/save             → JSON {markdown, filename} → saves to ~/Downloads
"""
import os
import sys
import re
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template

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

YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?.*v=|youtu\.be/)([A-Za-z0-9_\-]{11})"
)


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def convert_youtube(url: str) -> str:
    """Extract YouTube video info + transcript via yt-dlp."""
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title       = info.get("title", "Unknown Title")
        uploader    = info.get("uploader", "Unknown")
        duration    = info.get("duration", 0)
        view_count  = info.get("view_count", 0)
        description = info.get("description", "")
        upload_date = info.get("upload_date", "")
        like_count  = info.get("like_count", "N/A")
        tags        = info.get("tags", [])
        webpage_url = info.get("webpage_url", url)

        # Format duration
        mins, secs = divmod(int(duration), 60)
        hrs, mins = divmod(mins, 60)
        dur_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"

        # Format date
        if len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

        # Try to get transcript via youtube-transcript-api
        transcript_md = ""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api.formatters import TextFormatter
            match = YOUTUBE_RE.search(url)
            if match:
                video_id = match.group(1)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # prefer manual, fall back to auto-generated
                try:
                    transcript = transcript_list.find_manually_created_transcript(
                        ["tr", "en", "en-US", "en-GB"]
                    )
                except Exception:
                    try:
                        transcript = transcript_list.find_generated_transcript(
                            ["tr", "en", "en-US"]
                        )
                    except Exception:
                        transcript = next(iter(transcript_list))

                entries = transcript.fetch()
                lines = []
                for entry in entries:
                    t = entry.get("start", 0)
                    m, s = divmod(int(t), 60)
                    h, m = divmod(m, 60)
                    ts = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                    text = entry.get("text", "").replace("\n", " ").strip()
                    if text:
                        lines.append(f"**[{ts}]** {text}")
                if lines:
                    transcript_md = "\n\n## Transcript\n\n" + "\n\n".join(lines)
        except Exception as te:
            transcript_md = f"\n\n> ⚠️ Transcript not available: {te}"

        # Build markdown
        desc_short = (description[:800] + "…") if len(description) > 800 else description
        tags_str = ", ".join(f"`{t}`" for t in tags[:10]) if tags else "_none_"

        markdown = f"""# {title}

| Field       | Value |
|-------------|-------|
| **Channel** | {uploader} |
| **Duration**| {dur_str} |
| **Views**   | {view_count:,} |
| **Likes**   | {like_count} |
| **Date**    | {upload_date} |
| **URL**     | [{webpage_url}]({webpage_url}) |

## Description

{desc_short}

## Tags

{tags_str}
{transcript_md}
"""
        return markdown.strip()

    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"YouTube conversion failed: {e}") from e


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

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    tmp_path = None
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
        if tmp_path:
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
        # YouTube: use dedicated converter
        if YOUTUBE_RE.search(url):
            markdown_text = convert_youtube(url)
            match = YOUTUBE_RE.search(url)
            video_id = match.group(1) if match else "video"
            return jsonify({
                "markdown": markdown_text,
                "filename": f"youtube-{video_id}.md",
                "chars": len(markdown_text),
            })

        # Generic URL
        result = md.convert(url)
        markdown_text = result.text_content
        return jsonify({
            "markdown": markdown_text,
            "filename": "converted-url.md",
            "chars": len(markdown_text),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/save", methods=["POST"])
def save_file():
    """Save markdown directly to ~/Downloads/{filename}-converted.md"""
    data = request.get_json(force=True, silent=True) or {}
    markdown = data.get("markdown", "")
    raw_name = data.get("filename", "converted")

    # Strip existing extension then append -converted.md
    base = raw_name.rsplit(".", 1)[0] if "." in raw_name else raw_name
    safe_base = re.sub(r'[^\w\-.]', '_', base)
    out_name = f"{safe_base}-converted.md"

    downloads_dir = os.path.expanduser("~/Downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    out_path = os.path.join(downloads_dir, out_name)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        return jsonify({"path": out_path, "filename": out_name})
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})
