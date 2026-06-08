# mdConvertor.spec — PyInstaller spec file
# Use --onedir (not --onefile) for better macOS stability.

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

platform_hidden_imports = []
if sys.platform == 'darwin':
    platform_hidden_imports.append('webview.platforms.cocoa')
elif sys.platform == 'win32':
    platform_hidden_imports.extend(['webview.platforms.winforms', 'webview.platforms.edgehtml'])

# Collect all markitdown data/submodule files
markitdown_datas = collect_data_files('markitdown')
markitdown_hidden = collect_submodules('markitdown')

# Collect magika ML model files (required by MarkItDown for file-type detection)
magika_datas = collect_data_files('magika')

# Collect onnxruntime data files (required by magika)
try:
    onnx_datas = collect_data_files('onnxruntime')
except Exception:
    onnx_datas = []

# Collect markitdown converter data
try:
    mammoth_datas = collect_data_files('mammoth')
except Exception:
    mammoth_datas = []

# Collect yt-dlp data files (YouTube extractor plugins)
try:
    ytdlp_datas = collect_data_files('yt_dlp')
    ytdlp_hidden = collect_submodules('yt_dlp')
except Exception:
    ytdlp_datas = []
    ytdlp_hidden = []

# ebooklib for EPub support
try:
    epub_datas = collect_data_files('ebooklib')
except Exception:
    epub_datas = []

# markitdown-ocr metadata and submodules
try:
    ocr_metadata = copy_metadata('markitdown-ocr')
    ocr_hidden = collect_submodules('markitdown_ocr')
except Exception:
    ocr_metadata = []
    ocr_hidden = []

# Include template folder
templates_src = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'templates')

a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=[],
    datas=[
        (templates_src, 'templates'),
        *markitdown_datas,
        *magika_datas,
        *onnx_datas,
        *mammoth_datas,
        *ytdlp_datas,
        *epub_datas,
        *ocr_metadata,
    ],
    hiddenimports=[
        'markitdown',
        'markitdown._markitdown',
        'flask',
        'webview',
        *platform_hidden_imports,
        'jinja2',
        'werkzeug',
        'magika',
        'onnxruntime',
        'onnxruntime.capi._pybind_state',
        'mammoth',
        'openpyxl',
        'pptx',
        'docx',
        'pandas',
        'PIL',
        'speech_recognition',
        'pydub',
        'chardet',
        'charset_normalizer',
        'ebooklib',
        'extract_msg',
        'yt_dlp',
        'youtube_transcript_api',
        'pdfminer',
        'pdfplumber',
        'xlrd',
        'lxml',
        'fitz',
        'openai',
        *markitdown_hidden,
        *ytdlp_hidden,
        *ocr_hidden,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out pocketsphinx-data and non-macOS binaries to save space
a.datas = [d for d in a.datas if 'pocketsphinx-data' not in d[0] and 'pocketsphinx-data' not in d[1] and not any(x in d[0] for x in ['flac-linux', 'flac-win32.exe'])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mdConvertor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,    # No terminal window on macOS
    codesign_identity=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mdConvertor',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='mdConvertor.app',
        icon=None,
        bundle_identifier='com.mdconvertor.app',
        info_plist={
            'CFBundleDisplayName': 'mdConvertor',
            'CFBundleShortVersionString': '1.4.3',
            'CFBundleVersion': '1.4.3',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
