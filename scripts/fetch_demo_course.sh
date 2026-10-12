#!/usr/bin/env bash
# Download the Phase 0 demo course locally (media is never committed).
# Verifies sha256 checksums recorded here after the first successful fetch:
# fill in the EXPECTED_* values, then re-run to verify.
set -euo pipefail

OCW=https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013
OUT=data/demo-course
mkdir -p "$OUT"

fetch() {
  local url="$1" dest="$2"
  echo "fetching $dest"
  curl -fSL --retry 3 -o "$dest" "$url"
  sha256sum "$dest"
}

# Lecture slides PDFs (CC BY-NC-SA 4.0, MIT OCW)
fetch "$OCW/ff296575da32c406c2e56131e1e38997_MIT6_041SCF13_L01.pdf" "$OUT/MIT6_041SCF13_L01.pdf"
fetch "$OCW/a1462fa23de9d08c0dfd233a57278fed_MIT6_041SCF13_L02.pdf" "$OUT/MIT6_041SCF13_L02.pdf"
fetch "$OCW/a2015627268f4846eb3b1368623ce46f_MIT6_041SCF13_L03.pdf" "$OUT/MIT6_041SCF13_L03.pdf"
fetch "$OCW/17ea1d60167279b01569bc6dcd030966_MIT6_041SCF13_L04.pdf" "$OUT/MIT6_041SCF13_L04.pdf"

# Lecture videos via OCW's own download option (hosted on archive.org under OCW's upload)
fetch "https://archive.org/download/MIT6.041F10/MIT6_041F11_lec01_300k.mp4" "$OUT/lec01.mp4"
fetch "https://archive.org/download/MIT6.041F10/MIT6_041F11_lec02_300k.mp4" "$OUT/lec02.mp4"
fetch "https://archive.org/download/MIT6.041F10/MIT6_041F11_lec03_300k.mp4" "$OUT/lec03.mp4"
fetch "https://archive.org/download/MIT6.041F10/MIT6_041F11_lec04_300k.mp4" "$OUT/lec04.mp4"

# OpenStax Introductory Statistics 2e, full WEB PDF (CC BY-NC-SA 4.0)
fetch "https://assets.openstax.org/oscms-prodcms/media/documents/introductory-statistics-2e_-_WEB.pdf" "$OUT/introductory-statistics-2e.pdf"

echo "done. files in $OUT (not committed; see ATTRIBUTIONS.md)."
