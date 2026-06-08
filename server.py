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

# ── Configuration File helper ──────────────────────────────────────────────
CONFIG_PATH = os.path.expanduser("~/Library/Application Support/mdConvertor/config.json")

def read_config():
    import json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def write_config(data):
    import json
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ── Template directory (patched by main.py before import) ────────────────────
TEMPLATE_DIR = os.environ.get(
    "MDCONVERTOR_TEMPLATE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
)

# ── Claude (Anthropic) to OpenAI Client Adapter ──────────────────────────────
class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = self.Chat(api_key)

    class Chat:
        def __init__(self, api_key: str):
            self.completions = self.Completions(api_key)

        class Completions:
            def __init__(self, api_key: str):
                self.api_key = api_key

            def create(self, model: str, messages: list, **kwargs):
                import requests
                anthropic_content = []
                for msg in messages:
                    if msg.get("role") == "user":
                        content = msg.get("content")
                        if isinstance(content, list):
                            for item in content:
                                if item.get("type") == "text":
                                    anthropic_content.append({
                                        "type": "text",
                                        "text": item.get("text")
                                    })
                                elif item.get("type") == "image_url":
                                    img_url = item.get("image_url", {}).get("url", "")
                                    if img_url.startswith("data:"):
                                        header, data = img_url.split(",", 1)
                                        media_type = header.split(";")[0].split(":", 1)[1]
                                        anthropic_content.append({
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": data
                                            }
                                        })
                        elif isinstance(content, str):
                            anthropic_content.append({
                                "type": "text",
                                "text": content
                            })

                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }

                claude_model = model
                if "gpt" in model or not model:
                    claude_model = "claude-sonnet-4-6"

                payload = {
                    "model": claude_model,
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": anthropic_content
                        }
                    ]
                }

                resp = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
                resp.raise_for_status()
                res_data = resp.json()

                content_text = ""
                for content_block in res_data.get("content", []):
                    if content_block.get("type") == "text":
                        content_text += content_block.get("text", "")

                class Choice:
                    class Message:
                        def __init__(self, text):
                            self.content = text
                        def __str__(self):
                            return self.content
                    def __init__(self, text):
                        self.message = self.Message(text)

                class OpenAIStyleResponse:
                    def __init__(self, text):
                        self.choices = [Choice(text)]

                return OpenAIStyleResponse(content_text)

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024  # 256 MB upload limit

md = MarkItDown(enable_plugins=True)

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


# ── PDF Image Extraction + LLM Description ───────────────────────────────────
MIN_IMAGE_DIM = 50   # Skip images smaller than 50x50 (icons, separators)
MAX_IMAGES = 20      # Limit to prevent token budget overflow
# Prompts per language
_IMG_PROMPTS = {
    "en": "Write a detailed description of this image. If it contains a diagram, chart, or table, describe its structure and data. If it contains text, transcribe it.",
    "tr": "Bu görselin detaylı bir açıklamasını yaz. Eğer diyagram, grafik veya tablo içeriyorsa yapısını ve verilerini açıkla. Metin içeriyorsa metnin transkripsiyonunu yap.",
    "auto": "Write a detailed description of this image in the same language as any surrounding text. If it contains a diagram, chart, or table, describe its structure and data. If it contains text, transcribe it.",
}

def _call_llm_for_image(llm_client, llm_model, img_b64: str, mime_type: str, lang: str = "en") -> str:
    """Send a single image to the LLM and return a text description."""
    prompt = _IMG_PROMPTS.get(lang, _IMG_PROMPTS["en"])
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{img_b64}",
                    },
                },
            ],
        }
    ]
    try:
        response = llm_client.chat.completions.create(model=llm_model, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"[Image description failed: {e}]"


def extract_pdf_images_with_descriptions(pdf_path: str, llm_client, llm_model: str, lang: str = "en") -> dict:
    """
    Extract images from a PDF using PyMuPDF, send each to the LLM for
    description, and return a dict mapping page numbers to descriptions.
    Returns: {page_number: ["description1", "description2", ...]}
    """
    import fitz  # PyMuPDF
    import base64

    descriptions = {}  # {page_num (1-indexed): [desc, ...]}
    image_count = 0

    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            if image_count >= MAX_IMAGES:
                break
            page = doc[page_num]
            images = page.get_images(full=True)
            for img_info in images:
                if image_count >= MAX_IMAGES:
                    break
                xref = img_info[0]
                try:
                    base_img = doc.extract_image(xref)
                except Exception:
                    continue
                # Skip tiny images (icons, bullets, separators)
                if base_img["width"] < MIN_IMAGE_DIM or base_img["height"] < MIN_IMAGE_DIM:
                    continue
                img_b64 = base64.b64encode(base_img["image"]).decode("utf-8")
                ext = base_img["ext"]
                mime_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
                desc = _call_llm_for_image(llm_client, llm_model, img_b64, mime_type, lang)
                descriptions.setdefault(page_num + 1, []).append(desc)
                image_count += 1
        doc.close()
    except Exception as e:
        print(f"[PDF image extraction error]: {e}", flush=True)

    return descriptions


def _merge_image_descriptions(markdown_text: str, descriptions: dict, lang: str = "en") -> str:
    """
    Insert image descriptions into the markdown at the correct page positions.
    Looks for '## Page N' headings and appends descriptions after each page's content.
    """
    if not descriptions:
        return markdown_text

    # Labels per language
    lbl_img = "Image" if lang != "tr" else "Görsel"
    lbl_page = "Page" if lang != "tr" else "Sayfa"

    import re as _re
    # Split markdown by page headings
    page_pattern = _re.compile(r"(## Page (\d+))")
    parts = page_pattern.split(markdown_text)

    # parts structure: [before, heading, num, content, heading, num, content, ...]
    if len(parts) < 4:
        # No page headings found — append all descriptions at the end
        extras = []
        for pg, descs in sorted(descriptions.items()):
            for i, desc in enumerate(descs, 1):
                extras.append(f"\n\n> 📷 **{lbl_img} {i} ({lbl_page} {pg}):** {desc}")
        return markdown_text + "\n".join(extras)

    # Rebuild markdown with descriptions injected
    result = parts[0]  # Content before first page heading
    i = 1
    while i < len(parts):
        heading = parts[i]       # "## Page N"
        page_num = int(parts[i + 1])  # N
        content = parts[i + 2] if i + 2 < len(parts) else ""

        result += heading + content

        # Append image descriptions for this page
        if page_num in descriptions:
            for j, desc in enumerate(descriptions[page_num], 1):
                result += f"\n\n> 📷 **{lbl_img} {j} ({lbl_page} {page_num}):** {desc}"
            result += "\n"

        i += 3

    return result


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
            "cachedir": False,  # Disable caching to prevent disk clutter
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

        # Try to get transcript via yt-dlp subtitles/automatic_captions URLs
        transcript_md = ""
        try:
            import requests

            # 1. Determine available captions
            captions_dict = info.get("subtitles") or {}
            # Fall back to automatic captions if no manual subtitles
            if not captions_dict:
                captions_dict = info.get("automatic_captions") or {}

            # 2. Prefer Turkish ('tr'), then English ('en', 'en-US', 'en-GB'), then default to the first language available
            target_lang = None
            for lang in ["tr", "tr-orig", "en", "en-US", "en-GB"]:
                if lang in captions_dict:
                    target_lang = lang
                    break
            if not target_lang and captions_dict:
                target_lang = next(iter(captions_dict))

            if target_lang:
                formats = captions_dict[target_lang]
                json3_format = next((f for f in formats if f.get("ext") == "json3"), None)
                vtt_format = next((f for f in formats if f.get("ext") == "vtt"), None)

                if json3_format:
                    json3_url = json3_format.get("url")
                    resp = requests.get(json3_url, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()

                    lines = []
                    for ev in data.get("events", []):
                        t_ms = ev.get("tStartMs", 0)
                        segs = ev.get("segs", [])
                        text = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
                        if text:
                            # Format timestamp
                            t_seconds = t_ms // 1000
                            mins, secs = divmod(t_seconds, 60)
                            hrs, mins = divmod(mins, 60)
                            ts = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
                            lines.append(f"**[{ts}]** {text}")

                    if lines:
                        transcript_md = "\n\n## Transcript\n\n" + "\n\n".join(lines)
                elif vtt_format:
                    # Parse WebVTT format
                    vtt_url = vtt_format.get("url")
                    resp = requests.get(vtt_url, timeout=10)
                    resp.raise_for_status()
                    vtt_text = resp.text

                    lines = []
                    blocks = vtt_text.replace("\r\n", "\n").split("\n\n")
                    for block in blocks:
                        block = block.strip()
                        if not block or "-->" not in block:
                            continue
                        parts = block.split("\n")
                        time_line = parts[0]
                        ts = time_line.split("-->")[0].strip().split(".")[0]
                        if ts.startswith("00:"):
                            ts = ts[3:]
                        text_lines = [p.strip() for p in parts[1:] if p.strip()]
                        text = " ".join(text_lines)
                        if text:
                            lines.append(f"**[{ts}]** {text}")

                    if lines:
                        transcript_md = "\n\n## Transcript\n\n" + "\n\n".join(lines)
            else:
                transcript_md = "\n\n> ⚠️ Transcript not available: No subtitle tracks found."
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
    provider = request.form.get("provider", "openai").strip()
    key = request.form.get("key", "").strip()
    model = request.form.get("model", "").strip()
    base_url = request.form.get("base_url", "").strip()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        conv_kwargs = {}
        if key:
            try:
                if provider == "openai":
                    from openai import OpenAI
                    conv_kwargs["llm_client"] = OpenAI(api_key=key)
                    conv_kwargs["llm_model"] = model or "gpt-4o-mini"
                elif provider == "anthropic":
                    conv_kwargs["llm_client"] = ClaudeAdapter(api_key=key)
                    conv_kwargs["llm_model"] = model or "claude-sonnet-4-6"
                elif provider == "custom":
                    from openai import OpenAI
                    conv_kwargs["llm_client"] = OpenAI(api_key=key, base_url=base_url)
                    conv_kwargs["llm_model"] = model
            except Exception as e:
                return jsonify({"error": f"LLM client initialization failed: {e}"}), 400

        result = md.convert(tmp_path, **conv_kwargs)
        markdown_text = result.text_content

        # PDF image extraction + LLM description (only when API key is set)
        img_desc_lang = request.form.get("img_desc_lang", "en").strip() or "en"
        if ext == "pdf" and conv_kwargs.get("llm_client") and conv_kwargs.get("llm_model"):
            try:
                img_descs = extract_pdf_images_with_descriptions(
                    tmp_path, conv_kwargs["llm_client"], conv_kwargs["llm_model"], img_desc_lang
                )
                if img_descs:
                    markdown_text = _merge_image_descriptions(markdown_text, img_descs, img_desc_lang)
            except Exception as img_exc:
                print(f"[PDF image description error]: {img_exc}", flush=True)

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
        provider = data.get("provider", "openai").strip()
        key = data.get("key", "").strip()
        model = data.get("model", "").strip()
        base_url = data.get("base_url", "").strip()
        conv_kwargs = {}
        if key:
            try:
                if provider == "openai":
                    from openai import OpenAI
                    conv_kwargs["llm_client"] = OpenAI(api_key=key)
                    conv_kwargs["llm_model"] = model or "gpt-4o-mini"
                elif provider == "anthropic":
                    conv_kwargs["llm_client"] = ClaudeAdapter(api_key=key)
                    conv_kwargs["llm_model"] = model or "claude-sonnet-4-6"
                elif provider == "custom":
                    from openai import OpenAI
                    conv_kwargs["llm_client"] = OpenAI(api_key=key, base_url=base_url)
                    conv_kwargs["llm_model"] = model
            except Exception as e:
                return jsonify({"error": f"LLM client initialization failed: {e}"}), 400

        # Fetch generic URL with a browser User-Agent to bypass bot detection blocks
        import urllib.parse
        import requests
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()

        # Determine extension based on Content-Type or URL path
        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        
        mime_map = {
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.ms-powerpoint": ".ppt",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            "application/vnd.ms-excel": ".xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "text/csv": ".csv",
            "application/json": ".json",
            "text/html": ".html",
            "application/xml": ".xml",
            "text/xml": ".xml",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/x-m4a": ".m4a",
            "audio/flac": ".flac",
            "application/epub+zip": ".epub",
            "application/zip": ".zip",
            "text/plain": ".txt",
            "text/markdown": ".md",
        }

        ext = mime_map.get(content_type)
        if not ext:
            parsed = urllib.parse.urlparse(url)
            path_ext = os.path.splitext(parsed.path)[1].lower()
            if path_ext in ALLOWED_EXTENSIONS or (path_ext and path_ext[1:] in ALLOWED_EXTENSIONS):
                ext = path_ext if path_ext.startswith(".") else f".{path_ext}"
            else:
                ext = ".html"  # Default fallback

        # Use temporary file to convert
        tmp_url_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_url:
                tmp_url_path = tmp_url.name
                tmp_url.write(resp.content)

            result = md.convert(tmp_url_path, **conv_kwargs)
            markdown_text = result.text_content
            
            # Determine filename
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path) or "converted-url"
            if not filename.endswith(ext):
                filename = f"{filename}{ext}"
            # Ensure it outputs as markdown filename
            out_filename = filename.rsplit(".", 1)[0] + ".md"

            return jsonify({
                "markdown": markdown_text,
                "filename": out_filename,
                "chars": len(markdown_text),
            })
        finally:
            if tmp_url_path:
                try:
                    os.unlink(tmp_url_path)
                except Exception:
                    pass
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


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(read_config())


@app.route("/api/settings", methods=["POST"])
def save_settings_api():
    data = request.get_json(force=True, silent=True) or {}
    write_config(data)
    return jsonify({"status": "saved"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})
