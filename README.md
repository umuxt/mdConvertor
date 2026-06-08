# mdConvertor

> A native macOS desktop app that converts **PDF, Word, Excel, PowerPoint, images, audio, YouTube URLs, ZIP, EPub** and more into clean **Markdown** — in one click.

Built with [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft) · [PyWebView](https://pywebview.flowrl.com) · Flask

---

## ⬇️ Download & Install (macOS)

### 1. Download the latest release

👉 **[Download the latest macOS DMG](https://github.com/umuxt/mdConvertor/releases/latest)** — GitHub Releases

### 2. Install

1. Open the downloaded `.dmg` file
2. Drag **mdConvertor** → **Applications**
3. Eject the disk image

### 3. First launch (Gatekeeper bypass)

Because the app is not from the App Store, macOS will warn you on first launch:

**Option A — Right-click method (easiest):**
> Right-click `mdConvertor.app` in Applications → **Open** → Click **Open** in the dialog

**Option B — Terminal:**
```bash
xattr -cr /Applications/mdConvertor.app
```

After this, the app opens normally every time with a double-click.

> **macOS version:** Requires macOS 11 Big Sur or later (Apple Silicon & Intel supported)

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 📂 Multi-file Drop | Drop multiple files at once, then convert all |
| 🔗 YouTube & URLs | Extracts title, channel, views, description + transcript |
| ✂️ Split View | Raw Markdown + live rendered preview side by side |
| 🖼️ AI Image Descriptions | Extract images from PDFs and generate descriptions with custom language choice (English/Turkish/Auto) |
| ⬇️ Save to Downloads | Files saved as `originalname-converted.md` to `~/Downloads` |
| 🌑 Dark Mode | Premium glassmorphism UI |
| 📦 Native Window | WKWebView — no Electron, fast & lightweight |

### Supported Formats
`PDF` · `DOCX` · `PPTX` · `XLSX` · `XLS` · `CSV` · `JSON` · `HTML` · `PNG/JPG` · `MP3/WAV` · `EPub` · `Outlook .msg` · `ZIP` · `Jupyter .ipynb` · `YouTube URL` · `Wikipedia` · `RSS`

---

## 🖥 Platform Support

| Platform | Support |
|----------|---------|
| macOS (Apple Silicon + Intel) | ✅ Native `.app` available |
| Windows | 🔜 Planned |
| Linux | 🔜 Planned |

---

## 🚀 Developer Setup (run from source)

### Requirements
- Python 3.10 or later
- macOS (for PyWebView WKWebView)

### Steps

```bash
# 1. Clone
git clone https://github.com/umuxt/mdConvertor.git
cd mdConvertor

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

### Build .app Bundle

```bash
chmod +x build.sh
./build.sh
# → dist/mdConvertor.app
```

### Create DMG Installer

```bash
chmod +x create_dmg.sh
./create_dmg.sh
# → dist/mdConvertor-1.4.0-macOS.dmg
```

---

## 🗂️ Project Structure

```
mdConvertor/
├── main.py              # Entry point: Flask thread + PyWebView window
├── server.py            # Flask API (/api/convert, /api/convert-url, /api/save)
├── templates/
│   └── index.html       # Full UI (drag & drop, dark mode, split panels)
├── requirements.txt     # Python dependencies
├── build.sh             # PyInstaller build script
├── create_dmg.sh        # DMG installer creator
├── mdConvertor.spec     # PyInstaller spec (onedir, sys._MEIPASS)
└── RELEASE_NOTES.md     # Release changelog
```

---

## 🛠️ Tech Stack

- **Conversion engine**: [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft) — 18 format converters
- **Desktop window**: [PyWebView](https://pywebview.flowrl.com) — native macOS WKWebView
- **API**: Flask (runs locally, no network required)
- **YouTube**: yt-dlp + youtube-transcript-api
- **Packaging**: PyInstaller (onedir `.app` bundle)
- **UI**: Vanilla HTML/CSS/JS + marked.js

---

## 📄 License

MIT
