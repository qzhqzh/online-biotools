#!/usr/bin/env bash

set -euo pipefail

INPUT_FILE="${1:-input.vcf}"
OUTPUT_FILE="${2:-test_data/vep_output.txt}"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE" >&2
  exit 1
fi

if [[ ! -d "vep_data/homo_sapiens/115_GRCh38" ]]; then
  echo "VEP cache directory missing: vep_data/homo_sapiens/115_GRCh38" >&2
  echo "Extract vep_data/homo_sapiens_vep_115_GRCh38.tar.gz into vep_data first." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

docker compose run --rm vep bash -lc '
  vep \
    --offline \
    --cache \
    --dir_cache /opt/vep/.vep \
    --species homo_sapiens \
    --assembly GRCh38 \
    --no_stats \
    --input_file /test/'"$INPUT_FILE"' \
    --output_file /test/'"$OUTPUT_FILE"'
'

echo "VEP output written to $OUTPUT_FILE"