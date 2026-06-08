## What's New in v1.4.3

This release updates the project versioning metadata and ensures all workflow configuration changes are correctly pushed to GitHub.

### ⚙️ CI/CD Updates
- **Workflow Build Fix:** Corrected action step references in the GitHub Actions configuration to ensure successful remote builds for both macOS and Windows.

---

## What's New in v1.4.2

This release fixes the Flask request context unbound error during real-time streaming conversion, ensuring a seamless and error-free execution flow.

### 🐛 Bug Fixes
- **Request Context Bug Fix:** Fixed a critical issue where conversion would fail (yielding 0 characters) due to a Flask request context unbound error by pre-saving uploaded files outside the generator.
- **Workflow Version Upgrade:** Upgraded GitHub Action steps in `.github/workflows/build.yml` to the latest versions to resolve runner deprecation blocks.

---

## What's New in v1.4.1

This release adds real-time conversion progress logs, a visual progress bar, and significant reliability and performance improvements.

### ✨ Features & Bug Fixes
- **Real-Time Progress & Logs:** Users can now view step-by-step progress logs and a progress bar directly in the UI during conversion, indicating the current status (e.g. text extraction, image scanning, AI description progress).
- **Parallel AI Descriptions:** Spearheaded parallel execution of LLM image description requests, vastly reducing wait times on PDFs with multiple images.
- **Request Context Bug Fix:** Fixed a critical issue where conversion would fail (yielding 0 characters) due to a Flask request context unbound error.
- **Cross-Platform Compatibility:** Adjusted local storage paths to dynamically adapt to Windows (`%APPDATA%`), macOS (`~/Library/Application Support`), and Linux, and prepared the PyInstaller spec file for Windows builds.
- **Automated CI/CD Workflows:** Added a GitHub Actions workflow to build and package both macOS `.dmg` and Windows `.zip` binaries automatically on release tags.

---

## What's New in v1.4.0

This release introduces native PDF image extraction and AI-powered image descriptions with language support.

### ✨ Features & Upgrades
- **PDF Image Extraction & Descriptions:** Native extraction of images from PDF pages using PyMuPDF and automatically generating descriptions/captions using LLMs (Claude, GPT-4o, etc.) when an API key is provided.
- **Image Description Language Selector:** Added a dropdown selector in the Settings panel. Users can choose English, Turkish, or "Auto" (matches the primary document language) for AI-generated image descriptions.
- **Seamless Inline Markdown Insertion:** Injects generated image descriptions right below the text of the page where the image was extracted.

---

## What's New in v1.3.0

This release fixes external web services integration, resolves bot-detection blocks, robustifies YouTube transcription, and enables persistent local storage for API settings.

### 🐛 Bug Fixes & Service Upgrades
- **Settings Persistence (API Key & Model):** Fixed the settings drawer not saving the entered API Key or provider model on app reload. Disabled private mode in PyWebView and set a dedicated App Support storage directory so values are remembered forever.
- **Robust YouTube Transcript Retrieval:** Replaced the legacy `youtube-transcript-api` (which returned empty XML parsing errors due to anti-bot rate-limiting) with a native `yt-dlp` timedtext extractor that fetches and parses `json3`/`vtt` subtitle streams natively using `requests`.
- **Wikipedia & URL Fetching Fixes (User-Agent):** Requests for generic URLs (like Wikipedia) are now fetched using a standard browser `User-Agent` to bypass scraper blocking (`403 Forbidden`). Fetched assets are written to a temporary file before being converted.

---

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
