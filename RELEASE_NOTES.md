## What's New in v1.1.0

This release brings size optimizations, cleaner resource management, and AI-powered Vision OCR capabilities.

### ✨ Features & Optimizations
- **Optional OpenAI Vision OCR Settings:** Added a collapsible Settings Panel in the UI where users can paste their OpenAI API Key and select a model (e.g., `gpt-4o` or `gpt-4o-mini`). This enables:
  - Full-page OCR for scanned PDFs
  - Extracting text from images inside DOCX, PPTX, and XLSX files
  - Automated detailed descriptions/captions for image files
- **localStorage Saving:** Your API Key and model selections are automatically saved securely in the browser's localStorage.
- **Application Size Optimization (~42 MB saved):** Filtered out unused pocketsphinx dil dosyaları and non-macOS flac binary dependencies during packaging.
- **Zero yt-dlp Cache Clutter:** Disabled caching in `yt-dlp` to prevent writing clutter folders to `~/.cache/yt-dlp`.
- **Automatic Temp Cleanup:** Uploaded files are immediately deleted from temporary storage right after conversion, ensuring zero system pollution.

---

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
1. Download `mdConvertor-x.x.x-macOS.dmg`
2. Open the DMG → drag **mdConvertor** to **Applications**
3. **First launch:** Right-click → Open (to bypass Gatekeeper on unsigned apps)

### 🛠 Tech Stack
- [MarkItDown](https://github.com/microsoft/markitdown) (Microsoft) — conversion engine
- [PyWebView](https://pywebview.flowrl.com) — native WKWebView window
- Flask — local API server
- PyInstaller — macOS packaging
