#!/bin/bash
# Download Ensembl VEP indexed cache into ./data/vep (or $CACHE_DIR).
# Usage:
#   bash scripts/download_vep_cache.sh              # merged GRCh37 (default)
#   bash scripts/download_vep_cache.sh merged GRCh37
#   bash scripts/download_vep_cache.sh merged GRCh38
#   bash scripts/download_vep_cache.sh ensembl GRCh37

set -euo pipefail

CACHE_TYPE="${1:-merged}"
ASSEMBLY="${2:-GRCh37}"
CACHE_DIR="${CACHE_DIR:-./data/vep}"

case "$ASSEMBLY" in
  GRCh37)
    FTP_BASE="https://ftp.ensembl.org/pub/grch37/current/variation/indexed_vep_cache"
    VER="116_GRCh37"
    ;;
  GRCh38)
    FTP_BASE="https://ftp.ensembl.org/pub/release-116/variation/indexed_vep_cache"
    VER="116_GRCh38"
    ;;
  *)
    echo "Unknown assembly: $ASSEMBLY (use GRCh37 or GRCh38)"
    exit 1
    ;;
esac

case "$CACHE_TYPE" in
  merged) FILE="homo_sapiens_merged_vep_${VER}.tar.gz" ;;
  ensembl) FILE="homo_sapiens_vep_${VER}.tar.gz" ;;
  refseq) FILE="homo_sapiens_refseq_vep_${VER}.tar.gz" ;;
  *)
    echo "Unknown cache type: $CACHE_TYPE (merged|ensembl|refseq)"
    exit 1
    ;;
esac

URL="${FTP_BASE}/${FILE}"
TARGET="${CACHE_DIR}/${FILE}"
mkdir -p "$CACHE_DIR"

echo "Downloading $FILE -> $TARGET"
if [ -f "$TARGET" ]; then
  echo "File exists, skip download. Delete to re-fetch."
else
  curl -L --progress-bar -C - -o "$TARGET" "$URL"
fi

echo "Extracting into $CACHE_DIR ..."
tar -xzf "$TARGET" -C "$CACHE_DIR"
echo "Done. Point VEP_CACHE_DIR=$CACHE_DIR and restart web."
