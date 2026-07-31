"""Helpers to prefer MANE / canonical transcripts across engines."""

from __future__ import annotations

from typing import Any

from apps.annotations.knowledge import store as knowledge_store


def strip_accession_version(acc: str) -> str:
    return acc.split(".", 1)[0].strip()


def mane_rank_from_accession(accession: str | None) -> int:
    """0 = MANE Select, 1 = Plus Clinical, 100 = not MANE / unknown."""
    if not accession:
        return 100
    rec = knowledge_store.lookup_transcript(strip_accession_version(accession))
    if not rec or not rec.get("mane"):
        return 100
    if rec.get("mane_status") == "select":
        return 0
    return 1


def mane_rank_from_vep_tc(tc: dict[str, Any]) -> int:
    """Prefer VEP native MANE flags, then local MANE knowledge map."""
    if (
        tc.get("mane_select") in (1, "1", True)
        or tc.get("MANE_SELECT") in (1, "1", True)
        or str(tc.get("mane") or "").upper() in {"MANE_SELECT", "SELECT", "MANE SELECT"}
    ):
        return 0
    if (
        tc.get("mane_plus_clinical") in (1, "1", True)
        or tc.get("MANE_PLUS_CLINICAL") in (1, "1", True)
        or str(tc.get("mane") or "").upper()
        in {"MANE_PLUS_CLINICAL", "PLUS_CLINICAL", "MANE PLUS CLINICAL"}
    ):
        return 1
    return mane_rank_from_accession(tc.get("transcript_id"))


def is_refseq_accession(accession: str | None) -> bool:
    """True for RefSeq transcript IDs (NM_/NR_/XM_/XR_)."""
    if not accession:
        return False
    acc = strip_accession_version(accession).upper()
    return acc.startswith(("NM_", "NR_", "XM_", "XR_"))


def pick_reason_for_rank(
    rank: int, *, canonical: bool = False, refseq: bool = False
) -> str:
    if rank == 0:
        return "mane_select_nm" if refseq else "mane_select"
    if rank == 1:
        return "mane_plus_clinical_nm" if refseq else "mane_plus_clinical"
    if canonical:
        return "canonical"
    return "first_listed"


def sort_key_for_transcript(
    mane_rank: int,
    canonical: bool,
    index: int,
    *,
    refseq: bool = False,
) -> tuple:
    """Lower is better.

    Order: MANE Select → Plus Clinical → (within same MANE tier: NM before ENST)
    → Ensembl canonical → original order.
    """
    if mane_rank < 100:
        # Within MANE: RefSeq NM first, then ENST / others
        return (mane_rank, 0 if refseq else 1, index)
    canon_penalty = 0 if canonical else 1
    return (50 + canon_penalty, 0 if refseq else 1, index)
