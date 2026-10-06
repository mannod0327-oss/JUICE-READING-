#!/usr/bin/env bash
# Render the four PDFs to PNG (200 dpi) and crop every picture the units use.
#   JR_PDF_DIR=/path/to/pdfs bash tools/media.sh        (PDF names must end with _1.pdf … _4.pdf)
# Output: build/pages/b{1..4}/p-NN.png and build/media/*.jpg (+ media-jr{N}.json manifests)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/pages build/media
for b in 1 2 3 4; do
  if [ ! -f "build/pages/b$b/p-81.png" ]; then
    pdf=$(ls "${JR_PDF_DIR:?set JR_PDF_DIR to the folder with the four PDFs}"/*_"$b".pdf | head -1)
    mkdir -p "build/pages/b$b"
    pdftoppm -r 200 -png "$pdf" "build/pages/b$b/p"
  fi
done
mkdir -p build/tmp
for b in 1 2 3 4; do
  OMP_THREAD_LIMIT=1 TMPDIR=build/tmp python3 -I tools/extract_media.py "build/pages/b$b" "content/book$b.json" build/media &
done
wait
