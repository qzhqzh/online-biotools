#!/bin/bash
# =============================================================================
# VEP Cache Download Script for hg19 (GRCh37)
# =============================================================================
# Downloads the Ensembl VEP cache for GRCh37 (hg19).
#
# Cache options (choose ONE):
#
#   1. homo_sapiens_merged_vep_116_GRCh37.tar.gz  (~24.5 GB)  [RECOMMENDED]
#      Merged Ensembl + RefSeq transcripts, best coverage for c./p. annotation.
#
#   2. homo_sapiens_vep_116_GRCh37.tar.gz          (~22.8 GB)
#      Ensembl transcripts only.
#
#   3. homo_sapiens_refseq_vep_116_GRCh37.tar.gz   (~22.2 GB)
#      RefSeq transcripts only.
#
# Usage:
#   bash scripts/download_cache.sh          # download merged (recommended)
#   bash scripts/download_cache.sh ensembl  # Ensembl only
#   bash scripts/download_cache.sh refseq   # RefSeq only
# =============================================================================

set -euo pipefail

CACHE_DIR="${CACHE_DIR:-./cache}"
FTP_BASE="https://ftp.ensembl.org/pub/grch37/current/variation/indexed_vep_cache"

# Choose cache type
CACHE_TYPE="${1:-merged}"

case "$CACHE_TYPE" in
    merged)
        FILE="homo_sapiens_merged_vep_116_GRCh37.tar.gz"
        ;;
    ensembl)
        FILE="homo_sapiens_vep_116_GRCh37.tar.gz"
        ;;
    refseq)
        FILE="homo_sapiens_refseq_vep_116_GRCh37.tar.gz"
        ;;
    *)
        echo "Unknown cache type: $CACHE_TYPE"
        echo "Usage: $0 [merged|ensembl|refseq]"
        exit 1
        ;;
esac

URL="${FTP_BASE}/${FILE}"
TARGET="${CACHE_DIR}/${FILE}"

mkdir -p "$CACHE_DIR"

echo "============================================"
echo " VEP Cache Download"
echo "============================================"
echo " Cache type : $CACHE_TYPE"
echo " URL        : $URL"
echo " Target     : $TARGET"
echo " Cache dir  : $CACHE_DIR"
echo "============================================"

if [ -f "$TARGET" ]; then
    echo "File already exists: $TARGET"
    echo "To re-download, delete it first: rm $TARGET"
    exit 0
fi

# Check available space (need ~30GB free for download + extraction)
AVAIL_KB=$(df "$CACHE_DIR" | tail -1 | awk '{print $4}')
AVAIL_GB=$((AVAIL_KB / 1024 / 1024))
echo "Available disk space: ${AVAIL_GB} GB"

if [ "$AVAIL_GB" -lt 30 ]; then
    echo "WARNING: Less than 30GB available. Download may fail."
    echo "Continue? [y/N]"
    read -r confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ""
echo "Downloading $FILE ..."
echo "This will take a while (~24 GB). Progress will be shown."
echo ""

# Download with progress and resume support
curl -L --progress-bar -C - -o "$TARGET" "$URL"

echo ""
echo "Download complete!"
echo ""

# Extract
echo "Extracting cache to $CACHE_DIR ..."
tar -xzf "$TARGET" -C "$CACHE_DIR"

echo ""
echo "============================================"
echo " Cache ready!"
echo " Directory: $CACHE_DIR"
echo ""
echo " You can now start the service:"
echo "   docker compose up -d"
echo "============================================"
