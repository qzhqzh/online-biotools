"""Normalize common variant strings to VEP region format."""

from __future__ import annotations

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
    v = re.sub(r"^chr", "", v, flags=re.IGNORECASE)

    hgvs_match = re.match(r"^(\d+|X|Y|MT):g\.(\d+)([ACGT]+)>([ACGT]+)$", v, re.IGNORECASE)
    if hgvs_match:
        chrom, pos, ref, alt = hgvs_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    colon_match = re.match(
        r"^(\d+|X|Y|MT):(\d+)\s+([ACGT]+)[>/]([ACGT]+)$", v, re.IGNORECASE
    )
    if colon_match:
        chrom, pos, ref, alt = colon_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    space_match = re.match(
        r"^(\d+|X|Y|MT)\s+(\d+)\s+([ACGT]+)[>/]([ACGT]+)$", v, re.IGNORECASE
    )
    if space_match:
        chrom, pos, ref, alt = space_match.groups()
        return f"{chrom} {pos} {pos} {ref}/{alt} +"

    return v
