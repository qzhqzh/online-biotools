#!/bin/bash
# Download Ensembl VEP indexed cache into ./data/vep (or $CACHE_DIR).
# Usage:
#   bash scripts/download_vep_cache.sh              # merged GRCh37 (default)
#   bash scripts/download_vep_cache.sh merged GRCh37
#   bash scripts/download_vep_cache.sh merged GRCh38
#   bash scripts/download_vep_cache.sh ensembl GRCh37
# Background:
#   BACKGROUND=1 bash scripts/download_vep_cache.sh merged GRCh38

set -euo pipefail

CACHE_TYPE="${1:-merged}"
ASSEMBLY="${2:-GRCh37}"
CACHE_DIR="${CACHE_DIR:-./data/vep}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-${CACHE_DIR}/.downloads}"
BACKGROUND="${BACKGROUND:-0}"
MANAGED_PIDFILE="${MANAGED_PIDFILE:-0}"

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
mkdir -p "$CACHE_DIR" "$DOWNLOAD_DIR"
TARGET="${DOWNLOAD_DIR}/${FILE}"
LOG="${DOWNLOAD_DIR}/download_${VER}.log"
PIDFILE="${DOWNLOAD_DIR}/download_${VER}.pid"
MARKER="${DOWNLOAD_DIR}/download_${VER}.done"

cleanup_pidfile() {
  if [ "$MANAGED_PIDFILE" = "1" ]; then
    rm -f "$PIDFILE"
  fi
}

if [ "$MANAGED_PIDFILE" = "1" ]; then
  trap cleanup_pidfile EXIT INT TERM
fi

run_download() {
  echo "[$(date -Iseconds)] Downloading $FILE"
  echo "  URL: $URL"
  echo "  ->  $TARGET"
  if [ -f "$TARGET" ]; then
    echo "File exists, resume/skip via curl -C -"
  fi
  curl -L --progress-bar -C - -o "$TARGET" "$URL"

  # Expected extract layout: $CACHE_DIR/homo_sapiens_merged/${VER}/
  SPECIES_DIR="homo_sapiens_merged"
  if [ "$CACHE_TYPE" = "ensembl" ]; then SPECIES_DIR="homo_sapiens"; fi
  if [ "$CACHE_TYPE" = "refseq" ]; then SPECIES_DIR="homo_sapiens_refseq"; fi
  READY="${CACHE_DIR}/${SPECIES_DIR}/${VER}"

  if [ -d "$READY" ] && [ -f "${READY}/info.txt" ]; then
    echo "Already extracted at $READY"
  else
    echo "[$(date -Iseconds)] Extracting into $CACHE_DIR ..."
    tar -xzf "$TARGET" -C "$CACHE_DIR"
  fi

  if [ ! -f "${READY}/info.txt" ]; then
    echo "ERROR: expected cache missing after extract: $READY" >&2
    exit 1
  fi

  date -Iseconds > "$MARKER"
  echo "[$(date -Iseconds)] Done. Cache ready at $READY"
  echo "Point VEP_CACHE_DIR=$CACHE_DIR and restart web if needed."
}

if [ "$BACKGROUND" = "1" ]; then
  if [ -f "$PIDFILE" ]; then
    existing_pid="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
      echo "Download already running (pid $existing_pid). Log: $LOG"
      exit 0
    fi
    echo "Removing stale pid file: $PIDFILE"
    rm -f "$PIDFILE"
  fi
  if [ -f "$MARKER" ] && [ -d "${CACHE_DIR}/homo_sapiens_merged/${VER}" ]; then
    echo "Already complete ($MARKER). Skip."
    exit 0
  fi
  # Re-exec without BACKGROUND to avoid nested nohup loops. The child owns and
  # removes PIDFILE on normal exit, failure, SIGINT or SIGTERM.
  nohup env BACKGROUND=0 MANAGED_PIDFILE=1 CACHE_DIR="$CACHE_DIR" \
    DOWNLOAD_DIR="$DOWNLOAD_DIR" \
    bash "$0" "$CACHE_TYPE" "$ASSEMBLY" >"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  echo "Started background download pid=$(cat "$PIDFILE")"
  echo "  log: $LOG"
  echo "  tar: $TARGET"
  exit 0
fi

run_download
