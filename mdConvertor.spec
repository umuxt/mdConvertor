# mdConvertor.spec — PyInstaller spec file
# Use --onedir (not --onefile) for better macOS stability.

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

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
    ],
    hiddenimports=[
        'markitdown',
        'markitdown._markitdown',
        'flask',
        'webview',
        'webview.platforms.cocoa',
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
        *markitdown_hidden,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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

app = BUNDLE(
    coll,
    name='mdConvertor.app',
    icon=None,
    bundle_identifier='com.mdconvertor.app',
    info_plist={
        'CFBundleDisplayName': 'mdConvertor',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
