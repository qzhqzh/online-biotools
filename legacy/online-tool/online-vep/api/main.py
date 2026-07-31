"""
Online VEP (Variant Effect Predictor) REST API Service.

Supports hg19 (GRCh37) annotation, returning c. and p. HGVS notations.

Endpoints:
    POST /annotate       - Annotate variants
    GET  /health         - Health check
"""

import json
import os
import subprocess
import tempfile
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Online VEP Service",
    description="Variant Effect Predictor REST API - hg19 (GRCh37)",
    version="1.0.0",
)

# === Configuration ===
VEP_BIN = os.environ.get("VEP_BIN", "/opt/vep/src/ensembl-vep/vep")
VEP_CACHE_DIR = os.environ.get("VEP_CACHE_DIR", "/data/cache")
DEFAULT_ASSEMBLY = os.environ.get("VEP_ASSEMBLY", "GRCh37")

# Check cache exists (evaluated at request time)
def is_cache_ready() -> bool:
    if not os.path.isdir(VEP_CACHE_DIR):
        return False
    items = os.listdir(VEP_CACHE_DIR)
    # Filter out any non-cache files (like tar.gz)
    return any(not f.endswith('.tar.gz') and not f.endswith('.aria2') for f in items)


# === Models ===
class VariantInput(BaseModel):
    variants: List[str] = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Variant list. Supported formats: 'chr:pos ref>alt' (e.g., '17:43092951 G>A'), 'chr pos ref/alt', HGVS g. (e.g., '17:g.43092951G>A'), or VEP tab format",
        examples=[["13:32906732 G>A", "17:43092951 G>A"]],
    )
    assembly: str = Field(
        default="GRCh37",
        description="Reference assembly: GRCh37 (hg19) or GRCh38 (hg38)",
        pattern="^(GRCh37|GRCh38)$",
    )


class HGVSEntry(BaseModel):
    transcript: Optional[str] = None
    cdot: Optional[str] = None
    protein: Optional[str] = None


class VariantResult(BaseModel):
    input: str
    allele: Optional[str] = None
    gene: Optional[str] = None
    feature: Optional[str] = None
    consequence: Optional[str] = None
    impact: Optional[str] = None
    cdot: Optional[str] = None
    protein: Optional[str] = None
    biotype: Optional[str] = None
    canonical: Optional[str] = None


class AnnotateResponse(BaseModel):
    success: bool
    assembly: str
    results: List[VariantResult]
    errors: List[str] = []


# === Input normalization ===
import re

def normalize_variant(raw: str) -> str:
    """Convert common variant formats to VEP tab format (chr pos pos ref/alt +).

    Supported inputs:
      - 'chr17:43092951 G>A' or '17:43092951 G>A'
      - '17 43092951 G>A' or '17 43092951 G/A'
      - '17:g.43092951G>A' (HGVS genomic)
      - 'chr17 43092951 G>A'
    """
    v = raw.strip()
    # Remove 'chr' prefix
    v = re.sub(r'^chr', '', v, flags=re.IGNORECASE)

    # HGVS g. format: '17:g.43092951G>A'
    hgvs_match = re.match(r'^(\d+):g\.(\d+)([ACGT]+)>([ACGT]+)$', v)
    if hgvs_match:
        chrom, pos, ref, alt = hgvs_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    # chr:pos ref>alt: '17:43092951 G>A' -> convert to tab
    colon_match = re.match(r'^(\d+):(\d+)\s+([ACGT]+)[>/]([ACGT]+)$', v)
    if colon_match:
        chrom, pos, ref, alt = colon_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    # chr pos ref>alt or ref/alt: '17 43092951 G>A'
    space_match = re.match(r'^(\d+)\s+(\d+)\s+([ACGT]+)[>/]([ACGT]+)$', v)
    if space_match:
        chrom, pos, ref, alt = space_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    # Already in VEP format or HGVS c./transcript format, pass through
    return v


# === Helper: run VEP ===
def run_vep(variants: List[str], assembly: str) -> tuple:
    """Run VEP on a list of HGVS variants, return parsed JSON."""
    if not is_cache_ready():
        raise HTTPException(
            status_code=503,
            detail="VEP cache not found. Please download the cache first: run scripts/download_cache.sh",
        )

    # Normalize and write variants, keep mapping to original input
    normalized_map = {}  # normalized -> original
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        for v in variants:
            norm = normalize_variant(v)
            normalized_map[norm] = v.strip()
            f.write(norm + "\n")
        input_file = f.name

    output_file = input_file + ".json"

    cmd = [
        "perl", VEP_BIN,
        "--cache",
        "--merged",
        "--dir_cache", VEP_CACHE_DIR,
        "--assembly", assembly,
        "--hgvs",
        "--symbol",
        "--canonical",
        "--pick",
        "--no_stats",
        "--json",
        "-i", input_file,
        "-o", output_file,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"VEP failed (exit {result.returncode}): {stderr[:500]}")

        # Read JSON output (VEP --json outputs one JSON object per line)
        results = []
        with open(output_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))

        return results, normalized_map

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"VEP binary not found at {VEP_BIN}",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="VEP annotation timed out (>5 minutes)",
        )
    finally:
        # Cleanup temp files
        for tmp in [input_file, output_file]:
            if os.path.exists(tmp):
                os.remove(tmp)


# === Parse VEP JSON to simplified output ===
def parse_vep_output(raw: list, input_map: dict = None) -> List[VariantResult]:
    """Extract c. and p. HGVS from VEP JSON output."""
    results = []
    input_map = input_map or {}

    for entry in raw:
        vep_input = entry.get("input", "")
        # Use original user input if available, otherwise use VEP input
        display_input = input_map.get(vep_input, vep_input)
        transcript_consequences = entry.get("transcript_consequences", [])

        if not transcript_consequences:
            results.append(VariantResult(input=display_input))
            continue

        # VEP with --pick returns exactly one consequence per variant
        tc = transcript_consequences[0]

        results.append(
            VariantResult(
                input=display_input,
                allele=tc.get("variant_allele"),
                gene=tc.get("gene_symbol") or tc.get("gene_id"),
                feature=tc.get("transcript_id"),
                consequence=",".join(tc.get("consequence_terms", [])),
                impact=tc.get("impact"),
                cdot=tc.get("hgvsc"),   # c. notation
                protein=tc.get("hgvsp"), # p. notation
                biotype=tc.get("biotype"),
                canonical=("YES" if tc.get("canonical") == 1 else None),
            )
        )

    return results


# === Routes ===
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "cache_ready": is_cache_ready(),
        "assembly": DEFAULT_ASSEMBLY,
        "vep_bin": VEP_BIN,
    }


@app.post("/annotate", response_model=AnnotateResponse)
async def annotate(input: VariantInput):
    """Annotate variants and return c./p. HGVS notation.

    Accepts HGVS g. notation (e.g., 17:g.43092951G>A) or
    transcript c. notation (e.g., ENST00000366667:c.803C>T).
    """
    if not input.variants:
        raise HTTPException(status_code=400, detail="No variants provided")

    try:
        raw, input_map = run_vep(input.variants, input.assembly)
        results = parse_vep_output(raw, input_map)
        return AnnotateResponse(
            success=True,
            assembly=input.assembly,
            results=results,
        )
    except HTTPException:
        raise
    except Exception as e:
        return AnnotateResponse(
            success=False,
            assembly=input.assembly,
            results=[],
            errors=[str(e)],
        )


@app.get("/")
async def root():
    return {
        "service": "Online VEP",
        "version": "1.0.0",
        "assembly": DEFAULT_ASSEMBLY,
        "endpoints": {
            "annotate": "POST /annotate",
            "health": "GET /health",
        },
    }
