"""Local gene / MANE knowledge store loaded from data/knowledge/."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
import json
import re
import threading
from pathlib import Path
from typing import Any

from django.conf import settings

_lock = threading.Lock()
_genes: list[dict[str, Any]] | None = None
_transcript_records: dict[str, dict[str, Any]] | None = None
_meta: dict[str, Any] | None = None

_gene_rows: list[dict[str, Any]] | None = None
_gene_search_blobs: list[str] | None = None
_gene_symbol_keys: list[str] | None = None
_gene_exact: dict[str, list[int]] | None = None
_transcript_rows: list[dict[str, Any]] | None = None
_transcript_search_blobs: list[str] | None = None
_transcript_accession_keys: list[str] | None = None
_transcript_exact: dict[str, int] | None = None

_REFSEQ_RE = re.compile(r"^(NM|NR|NP|XM|XR)_?(\d+)$")
_ENSEMBL_RE = re.compile(r"^(ENST|ENSP|ENSG)_?(\d+)$")


def knowledge_dir() -> Path:
    return Path(
        getattr(settings, "KNOWLEDGE_DIR", settings.BASE_DIR / "data" / "knowledge")
    )


def normalize_accession(accession: str) -> str:
    """Normalize versioned and underscore-less RefSeq/Ensembl accessions."""

    raw = accession.strip().split(".", 1)[0].upper().replace(" ", "")
    match = _REFSEQ_RE.fullmatch(raw)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    match = _ENSEMBL_RE.fullmatch(raw)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return raw


def _load_meta() -> dict[str, Any]:
    path = knowledge_dir() / "meta.json"
    if not path.is_file():
        return {
            "ready": False,
            "error": "知识库尚未导入。请运行: python scripts/import_gene_knowledge.py",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ready": False, "error": f"知识库元数据无法读取: {exc}"}
    if not isinstance(data, dict):
        return {"ready": False, "error": "知识库元数据格式错误"}
    data["ready"] = True
    return data


def _load_genes() -> list[dict[str, Any]]:
    path = knowledge_dir() / "genes.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"invalid genes.jsonl JSON at line {line_number}: {exc.msg}"
                ) from exc
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _load_transcripts() -> dict[str, dict[str, Any]]:
    path = knowledge_dir() / "transcript-map.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid transcript-map.json: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("transcript-map.json must contain an object")
    if isinstance(data.get("records"), dict):
        return data["records"]
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("_") and isinstance(value, dict) and key != "meta"
    }


def _add_gene_exact(index: dict[str, list[int]], token: Any, row_index: int) -> None:
    value = str(token or "").strip().casefold()
    if not value:
        return
    bucket = index.setdefault(value, [])
    if row_index not in bucket:
        bucket.append(row_index)


def _build_indexes_locked() -> None:
    global _gene_rows, _gene_search_blobs, _gene_symbol_keys, _gene_exact
    global _transcript_rows, _transcript_search_blobs
    global _transcript_accession_keys, _transcript_exact

    gene_rows = sorted(
        _genes or [], key=lambda row: str(row.get("symbol") or "").casefold()
    )
    gene_search_blobs: list[str] = []
    gene_symbol_keys: list[str] = []
    gene_exact: dict[str, list[int]] = {}

    for index, gene in enumerate(gene_rows):
        symbol = str(gene.get("symbol") or "")
        synonyms = [str(value) for value in (gene.get("synonyms") or [])]
        fields = [
            symbol,
            gene.get("gene_id"),
            gene.get("ensembl_gene"),
            gene.get("hgnc_id"),
            gene.get("name"),
            *synonyms,
        ]
        gene_symbol_keys.append(symbol.casefold())
        gene_search_blobs.append(" ".join(str(value or "") for value in fields).casefold())
        for token in fields[:4] + synonyms:
            _add_gene_exact(gene_exact, token, index)

    transcript_rows: list[dict[str, Any]] = []
    for accession, record in (_transcript_records or {}).items():
        transcript_rows.append({"accession": accession, **record})
    transcript_rows.sort(key=lambda row: normalize_accession(str(row["accession"])))

    transcript_search_blobs: list[str] = []
    transcript_accession_keys: list[str] = []
    transcript_exact: dict[str, int] = {}
    for index, row in enumerate(transcript_rows):
        accession = normalize_accession(str(row.get("accession") or ""))
        aliases = [
            str(value)
            for value in (row.get("ensembl") or []) + (row.get("refseq") or [])
        ]
        transcript_accession_keys.append(accession)
        transcript_search_blobs.append(
            " ".join(
                [
                    accession,
                    str(row.get("gene") or ""),
                    str(row.get("gene_id") or ""),
                    str(row.get("note") or ""),
                    *aliases,
                ]
            ).upper()
        )
        for alias in [accession, *aliases]:
            normalized = normalize_accession(alias)
            if normalized:
                transcript_exact.setdefault(normalized, index)

    _gene_rows = gene_rows
    _gene_search_blobs = gene_search_blobs
    _gene_symbol_keys = gene_symbol_keys
    _gene_exact = gene_exact
    _transcript_rows = transcript_rows
    _transcript_search_blobs = transcript_search_blobs
    _transcript_accession_keys = transcript_accession_keys
    _transcript_exact = transcript_exact


def ensure_loaded() -> None:
    global _genes, _transcript_records, _meta
    if (
        _meta is not None
        and _genes is not None
        and _transcript_records is not None
        and _gene_rows is not None
        and _transcript_rows is not None
    ):
        return
    with _lock:
        if _meta is None:
            _meta = _load_meta()
        if _genes is None:
            _genes = _load_genes()
        if _transcript_records is None:
            _transcript_records = _load_transcripts()
        _build_indexes_locked()


def reload() -> None:
    global _genes, _transcript_records, _meta
    with _lock:
        _meta = _load_meta()
        _genes = _load_genes()
        _transcript_records = _load_transcripts()
        _build_indexes_locked()


def _require_indexes() -> None:
    if any(
        value is None
        for value in (
            _meta,
            _genes,
            _transcript_records,
            _gene_rows,
            _gene_search_blobs,
            _gene_symbol_keys,
            _gene_exact,
            _transcript_rows,
            _transcript_search_blobs,
            _transcript_accession_keys,
            _transcript_exact,
        )
    ):
        raise RuntimeError("knowledge store failed to initialize")


def get_meta() -> dict[str, Any]:
    ensure_loaded()
    _require_indexes()
    meta = dict(_meta or {})
    meta["gene_loaded"] = len(_gene_rows or [])
    meta["transcript_loaded"] = len(_transcript_rows or [])
    return meta


def _prefix_range(keys: list[str], needle: str) -> range:
    start = bisect_left(keys, needle)
    end = bisect_right(keys, needle + "\uffff")
    return range(start, end)


def search_genes(
    q: str = "",
    *,
    gene_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    ensure_loaded()
    _require_indexes()
    rows = _gene_rows or []
    blobs = _gene_search_blobs or []
    symbol_keys = _gene_symbol_keys or []
    exact = _gene_exact or {}
    needle = q.strip().casefold()

    if not needle:
        matched = [row for row in rows if not gene_type or row.get("type") == gene_type]
    else:
        candidate_indexes = list(exact.get(needle, []))
        candidate_indexes.extend(_prefix_range(symbol_keys, needle))
        candidate_indexes = list(dict.fromkeys(candidate_indexes))
        # Common symbol/accession searches use the prebuilt exact/prefix index.
        # Free-text name searches retain a pre-normalized scan fallback.
        if not candidate_indexes:
            candidate_indexes = list(range(len(rows)))

        scored: list[tuple[int, str, dict[str, Any]]] = []
        for index in candidate_indexes:
            gene = rows[index]
            if gene_type and gene.get("type") != gene_type:
                continue
            if needle not in blobs[index]:
                continue
            symbol = str(gene.get("symbol") or "")
            symbol_lower = symbol.casefold()
            gene_id = str(gene.get("gene_id") or "").casefold()
            ensembl = str(gene.get("ensembl_gene") or "").casefold()
            synonyms = [str(value).casefold() for value in (gene.get("synonyms") or [])]
            if symbol_lower == needle:
                rank = 0
            elif symbol_lower.startswith(needle):
                rank = 1
            elif gene_id == needle:
                rank = 2
            elif ensembl == needle or ensembl.startswith(needle):
                rank = 3
            elif any(value == needle or value.startswith(needle) for value in synonyms):
                rank = 4
            else:
                rank = 5
            scored.append((rank, symbol_lower, gene))
        scored.sort(key=lambda item: (item[0], item[1]))
        matched = [gene for _, _, gene in scored]

    total = len(matched)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": matched[offset : offset + limit],
    }


def search_transcripts(
    q: str = "",
    *,
    mane_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    ensure_loaded()
    _require_indexes()
    rows = _transcript_rows or []
    blobs = _transcript_search_blobs or []
    keys = _transcript_accession_keys or []
    exact = _transcript_exact or {}
    needle = normalize_accession(q) if q.strip() else ""

    if not needle:
        candidate_indexes = range(len(rows))
    elif needle in exact:
        candidate_indexes = [exact[needle]]
    else:
        prefix_indexes = list(_prefix_range(keys, needle))
        candidate_indexes = prefix_indexes or range(len(rows))

    matched: list[dict[str, Any]] = []
    for index in candidate_indexes:
        row = rows[index]
        if mane_only and not row.get("mane"):
            continue
        if needle and needle not in blobs[index]:
            continue
        matched.append(row)

    total = len(matched)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": matched[offset : offset + limit],
    }


def lookup_transcript(accession: str) -> dict[str, Any] | None:
    ensure_loaded()
    _require_indexes()
    normalized = normalize_accession(accession)
    index = (_transcript_exact or {}).get(normalized)
    if index is None:
        return None
    return dict((_transcript_rows or [])[index])
