#!/bin/sh
# Tesseract launcher: prefer this repo's user-space install under
# .tools/ (see scripts/setup_tesseract.sh), fall back to a system
# tesseract on PATH.
ROOT="$(cd "$(dirname "$0")/.." && pwd)/.tools/tesseract-root"
if [ -x "$ROOT/usr/bin/tesseract" ]; then
  LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu" \
  TESSDATA_PREFIX="$ROOT/usr/share/tesseract-ocr/5/tessdata" \
    exec "$ROOT/usr/bin/tesseract" "$@"
fi
exec tesseract "$@"
