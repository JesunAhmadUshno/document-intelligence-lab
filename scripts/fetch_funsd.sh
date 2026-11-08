#!/bin/sh
# Fetch the FUNSD corpus and verify it against the SHA-256 frozen
# in PREREGISTRATION.md before unpacking. The dataset lands in
# data/, which is gitignored: the dataset is never committed.
set -eu
cd "$(dirname "$0")/.."
mkdir -p data
EXPECTED="c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f"
if [ ! -f data/funsd.zip ]; then
  curl -sL -o data/funsd.zip https://guillaumejaume.github.io/FUNSD/dataset.zip
fi
ACTUAL="$(sha256sum data/funsd.zip | cut -d' ' -f1)"
if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "SHA-256 mismatch: got $ACTUAL" >&2
  exit 1
fi
if [ ! -d data/funsd/dataset ]; then
  python3 -c "import zipfile; zipfile.ZipFile('data/funsd.zip').extractall('data/funsd')"
fi
echo "FUNSD verified and unpacked under data/funsd/"
