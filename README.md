# mdConvertor

> A native macOS desktop application that converts PDF, Word, Excel, PowerPoint, images, audio, YouTube URLs, ZIP files, EPubs, and more into clean **Markdown** — in one click.

Built with [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft), [PyWebView](https://pywebview.flowrl.com) (native WKWebView), and Flask.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 📂 Drag & Drop | Drop any supported file onto the window |
| 🔗 URL Support | YouTube, web pages, and more |
| ✂️ Split View | Raw Markdown + live rendered preview side by side |
| 📋 Copy / Download | One-click copy or download as `.md` |
| 🌑 Dark Mode | Premium dark UI with glassmorphism |
| 📦 Native App | Runs as a real `.app` — no Electron overhead |

### Supported Formats
`PDF` · `DOCX` · `PPTX` · `XLSX` · `CSV` · `JSON` · `HTML` · `PNG/JPG` · `MP3/WAV` · `YouTube URL` · `ZIP` · `EPub`

---

## 🚀 Quick Start (Development)

### 1. Clone & enter the project
```bash
git clone git@github.com:umuxt/mdConvertor.git
cd mdConvertor
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python main.py
```

A native macOS window will open automatically.

---

## 🏗️ Build as `.app` Bundle

```bash
chmod +x build.sh
./build.sh
```

The bundle will be at `dist/mdConvertor.app`. Open it from Finder or:
```bash
open dist/mdConvertor.app
```

---

## 🗂️ Project Structure

```
mdConvertor/
├── main.py              # Entry point: Flask thread + PyWebView window
├── server.py            # Flask API (/api/convert, /api/convert-url)
├── templates/
│   └── index.html       # Full UI (drag & drop, dark mode, split panels)
├── requirements.txt     # Python dependencies
├── build.sh             # PyInstaller build script
└── mdConvertor.spec     # PyInstaller spec (onedir, sys._MEIPASS)
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+ · Flask · MarkItDown
- **Frontend**: Vanilla HTML/CSS/JS · marked.js (rendering)
- **Desktop Window**: PyWebView (native macOS WKWebView)
- **Packaging**: PyInstaller (onedir, `.app` bundle)

---

## 📸 Screenshot

> _Screenshot coming soon_

---

## 📄 License

MIT
