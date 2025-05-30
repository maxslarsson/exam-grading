#!/usr/bin/env bash
set -euo pipefail

# Base directory to search; default is current directory
BASE_DIR="${1:-.}"

# Find every .pdf (case-insensitive) and process it
find "$BASE_DIR" -type f \( -iname '*.pdf' \) -print0 \
  | while IFS= read -r -d '' pdf; do
      echo "Processing: $pdf"
      convert -density 150 "$pdf" "$pdf"
    done

