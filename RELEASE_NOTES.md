## What's New in v1.0.0

First public release of **mdConvertor** — a native macOS desktop app that converts any file to Markdown in seconds.

### ✨ Features
- **18 supported formats:** PDF, DOCX, PPTX, XLSX, XLS, CSV, JSON, HTML, PNG/JPG images, MP3/WAV audio, EPub, Outlook .msg, ZIP, Jupyter Notebook, YouTube URLs, Wikipedia, RSS feeds
- **Multi-file conversion:** Drop multiple files at once, queue them, convert all in one click
- **YouTube support:** Extracts title, channel, duration, views, description and transcript
- **Split view:** Raw Markdown + live rendered preview side by side
- **Save to Downloads:** Files saved as `originalname-converted.md` directly to `~/Downloads`
- **Premium dark UI:** Glassmorphism design, drag & drop, smooth animations
- **Native macOS window:** Uses WKWebView — no Electron, lightweight and fast

### 📦 Installation
1. Download `mdConvertor-1.0.0-macOS.dmg`
2. Open the DMG → drag **mdConvertor** to **Applications**
3. **First launch:** Right-click → Open (to bypass Gatekeeper on unsigned apps)

### 🛠 Tech Stack
- [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft) — conversion engine
- [PyWebView](https://pywebview.flowrl.com) — native WKWebView window
- Flask — local API server
- PyInstaller — macOS packaging
