#!/bin/bash
# scripts/install_fonts.sh
# Download and install Google handwriting fonts for the rendering engine

set -e

FONTS_DIR="/usr/share/fonts/truetype/google-fonts"
mkdir -p "$FONTS_DIR"

echo "📝 Installing handwriting fonts..."

# Font URLs from Google Fonts GitHub
BASE="https://github.com/google/fonts/raw/main/ofl"

declare -A FONTS=(
  ["Caveat-Regular.ttf"]="caveat/Caveat%5Bwght%5D.ttf"
  ["PatrickHand-Regular.ttf"]="patrickhand/PatrickHand-Regular.ttf"
  ["IndieFlower-Regular.ttf"]="indieflower/IndieFlower-Regular.ttf"
  ["ArchitectsDaughter-Regular.ttf"]="architectsdaughter/ArchitectsDaughter-Regular.ttf"
  ["DancingScript-Regular.ttf"]="dancingscript/DancingScript%5Bwght%5D.ttf"
)

for FILENAME in "${!FONTS[@]}"; do
  FONT_PATH="$FONTS_DIR/$FILENAME"
  if [ -f "$FONT_PATH" ]; then
    echo "  ✓ $FILENAME already exists"
    continue
  fi

  URL="${BASE}/${FONTS[$FILENAME]}"
  echo "  Downloading $FILENAME..."
  
  if curl -L --silent --output "$FONT_PATH" "$URL"; then
    echo "  ✓ Downloaded $FILENAME"
  else
    echo "  ⚠ Failed to download $FILENAME (will use fallback)"
    rm -f "$FONT_PATH"
  fi
done

# Update font cache
echo "🔄 Updating font cache..."
if command -v fc-cache &>/dev/null; then
  fc-cache -f -v "$FONTS_DIR" 2>/dev/null || true
fi

echo "✅ Font installation complete!"
echo ""
echo "Installed fonts:"
ls "$FONTS_DIR"/*.ttf 2>/dev/null | while read f; do echo "  - $(basename $f)"; done
