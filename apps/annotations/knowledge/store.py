"""Local gene / MANE knowledge store loaded from data/knowledge/."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from django.conf import settings

_lock = threading.Lock()
_genes: list[dict[str, Any]] | None = None
_transcript_records: dict[str, dict[str, Any]] | None = None
_meta: dict[str, Any] | None = None


def knowledge_dir() -> Path:
    return Path(
        getattr(settings, "KNOWLEDGE_DIR", settings.BASE_DIR / "data" / "knowledge")
    )


def _load_meta() -> dict[str, Any]:
    path = knowledge_dir() / "meta.json"
    if not path.is_file():
        return {
            "ready": False,
            "error": "知识库尚未导入。请运行: python scripts/import_gene_knowledge.py",
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    data["ready"] = True
    return data


def _load_genes() -> list[dict[str, Any]]:
    path = knowledge_dir() / "genes.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_transcripts() -> dict[str, dict[str, Any]]:
    path = knowledge_dir() / "transcript-map.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    return {
        k: v
        for k, v in data.items()
        if not k.startswith("_") and isinstance(v, dict) and k != "meta"
    }


def ensure_loaded() -> None:
    global _genes, _transcript_records, _meta
    if _meta is not None and _genes is not None and _transcript_records is not None:
        return
    with _lock:
        if _meta is None:
            _meta = _load_meta()
        if _genes is None:
            _genes = _load_genes()
        if _transcript_records is None:
            _transcript_records = _load_transcripts()


def reload() -> None:
    global _genes, _transcript_records, _meta
    with _lock:
        _meta = _load_meta()
        _genes = _load_genes()
        _transcript_records = _load_transcripts()


def get_meta() -> dict[str, Any]:
    ensure_loaded()
    assert _meta is not None
    meta = dict(_meta)
    meta["gene_loaded"] = len(_genes or [])
    meta["transcript_loaded"] = len(_transcript_records or [])
    return meta


def search_genes(
    q: str = "",
    *,
    gene_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    ensure_loaded()
    assert _genes is not None
    needle = q.strip().lower()
    scored: list[tuple[int, dict[str, Any]]] = []
    for g in _genes:
        if gene_type and g.get("type") != gene_type:
            continue
        symbol = str(g.get("symbol") or "")
        sym_l = symbol.lower()
        if needle:
            gene_id = str(g.get("gene_id") or "")
            ensembl = str(g.get("ensembl_gene") or "").lower()
            name = str(g.get("name") or "").lower()
            syns = [s.lower() for s in (g.get("synonyms") or [])]
            if (
                needle not in sym_l
                and needle != gene_id
                and needle not in ensembl
                and needle not in name
                and not any(needle in s for s in syns)
            ):
                continue
            # Rank: exact symbol > symbol prefix > gene_id > ensembl > synonym/name
            if sym_l == needle:
                rank = 0
            elif sym_l.startswith(needle):
                rank = 1
            elif gene_id == needle:
                rank = 2
            elif ensembl.startswith(needle) or needle in ensembl:
                rank = 3
            elif any(s == needle or s.startswith(needle) for s in syns):
                rank = 4
            else:
                rank = 5
            scored.append((rank, g))
        else:
            scored.append((0, g))

    scored.sort(key=lambda item: (item[0], item[1].get("symbol") or ""))
    matched = [g for _, g in scored]
    total = len(matched)
    page = matched[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": page,
    }


def search_transcripts(
    q: str = "",
    *,
    mane_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    ensure_loaded()
    assert _transcript_records is not None
    needle = q.strip().upper()
    rows: list[dict[str, Any]] = []
    for acc, rec in _transcript_records.items():
        if mane_only and not rec.get("mane"):
            continue
        if needle:
            linked = " ".join(
                (rec.get("ensembl") or []) + (rec.get("refseq") or [])
            ).upper()
            blob = f"{acc} {rec.get('gene', '')} {linked} {rec.get('note', '')}".upper()
            if needle not in blob:
                continue
        rows.append({"accession": acc, **rec})

    total = len(rows)
    page = rows[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": page,
    }


def lookup_transcript(accession: str) -> dict[str, Any] | None:
    ensure_loaded()
    assert _transcript_records is not None
    raw = accession.split(".", 1)[0].strip()
    upper = raw.upper()
    for key in (raw, upper):
        if key in _transcript_records:
            return {"accession": key, **_transcript_records[key]}
    # NM_/NP_ normalize
    if upper.startswith("NM"):
        key = "NM_" + upper.removeprefix("NM_").removeprefix("NM")
        if key in _transcript_records:
            return {"accession": key, **_transcript_records[key]}
    if upper.startswith("NP"):
        key = "NP_" + upper.removeprefix("NP_").removeprefix("NP")
        if key in _transcript_records:
            return {"accession": key, **_transcript_records[key]}
    return None
