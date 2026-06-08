#!/usr/bin/env bash
# create_dmg.sh — Creates a macOS .dmg installer for mdConvertor
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="mdConvertor"
VERSION="1.4.1"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"
DMG_PATH="dist/${DMG_NAME}"
STAGING_DIR="/tmp/${APP_NAME}_dmg_staging"

# ── Checks ────────────────────────────────────────────────────────────────────
if [ ! -d "$APP_BUNDLE" ]; then
  echo "❌  .app bundle not found at ${APP_BUNDLE}"
  echo "    Run ./build.sh first."
  exit 1
fi

echo "📦  Creating DMG installer: ${DMG_NAME}"

# ── Clean staging ─────────────────────────────────────────────────────────────
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy app bundle into staging
cp -r "$APP_BUNDLE" "$STAGING_DIR/${APP_NAME}.app"

# Create Applications symlink so users can drag-and-drop
ln -s /Applications "$STAGING_DIR/Applications"

# ── Create DMG with hdiutil ───────────────────────────────────────────────────
# Remove old DMG if exists
rm -f "$DMG_PATH"

hdiutil create \
  -volname "${APP_NAME} ${VERSION}" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  -imagekey zlib-level=9 \
  "$DMG_PATH"

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -rf "$STAGING_DIR"

echo ""
echo "✅  DMG created: ${DMG_PATH}"
echo "    Size: $(du -sh "${DMG_PATH}" | cut -f1)"
echo ""
echo "    To release on GitHub:"
echo "    gh release create v${VERSION} '${DMG_PATH}' --title 'mdConvertor v${VERSION}' --notes-file RELEASE_NOTES.md"
