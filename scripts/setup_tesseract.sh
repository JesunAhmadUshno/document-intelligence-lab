#!/bin/sh
# User-space Tesseract install, no root. This VM has no system
# tesseract and no sudo; the Ubuntu packages are fetched with a
# user-space apt state directory and unpacked (dpkg -x) under
# .tools/tesseract-root. On a machine with a system tesseract
# this script is unnecessary: scripts/tesseract.sh falls back
# to PATH.
set -eu
cd "$(dirname "$0")/.."
WORK=".tools/apt"
ROOT=".tools/tesseract-root"
mkdir -p "$WORK/lists/partial" "$WORK/cache/archives/partial" "$ROOT"
touch "$WORK/status"
APT="apt-get -o Dir::State::Lists=$PWD/$WORK/lists -o Dir::Cache=$PWD/$WORK/cache -o Dir::State::status=/var/lib/dpkg/status"
$APT update
mkdir -p "$WORK/debs"
$APT -y --download-only -o "Dir::Cache::Archives=$PWD/$WORK/debs" \
  install tesseract-ocr tesseract-ocr-eng
for d in "$WORK"/debs/*.deb; do dpkg -x "$d" "$ROOT"; done
scripts/tesseract.sh --version
