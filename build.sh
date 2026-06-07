#!/usr/bin/env bash
# build.sh — Package mdConvertor as a macOS .app bundle with PyInstaller
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨  Building mdConvertor.app …"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source ".venv/bin/activate"
fi

pyinstaller mdConvertor.spec --noconfirm

echo ""
echo "✅  Build complete!"
echo "    App bundle: dist/mdConvertor.app"
echo ""
echo "    To run:  open dist/mdConvertor.app"
