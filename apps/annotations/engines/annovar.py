"""ANNOVAR engine via local perl or dockerized CLI."""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.annotations.engines.base import (
    EngineFailed,
    EngineNotReady,
    EngineTimeout,
    UnsupportedAssembly,
)
from apps.annotations.engines.results import VariantResult
from apps.annotations.engines.transcript_prefer import (
    mane_rank_from_accession,
    pick_reason_for_rank,
)
from apps.annotations.normalize import normalize_variant

_annovar_semaphore: threading.Semaphore | None = None
_sem_lock = threading.Lock()

ASSEMBLY_TO_BUILDVER = {
    "GRCh37": "hg19",
    "GRCh38": "hg38",
    "hg19": "hg19",
    "hg38": "hg38",
}


def _semaphore() -> threading.Semaphore:
    global _annovar_semaphore
    with _sem_lock:
        if _annovar_semaphore is None:
            _annovar_semaphore = threading.Semaphore(settings.ANNOVAR_MAX_CONCURRENCY)
        return _annovar_semaphore


def db_root() -> Path:
    return Path(settings.ANNOVAR_DB_DIR)


def buildver_for_assembly(assembly: str) -> str:
    if assembly not in ASSEMBLY_TO_BUILDVER:
        raise UnsupportedAssembly(f"Unsupported assembly for ANNOVAR: {assembly}")
    return ASSEMBLY_TO_BUILDVER[assembly]


def is_db_ready(assembly: str) -> bool:
    try:
        buildver = buildver_for_assembly(assembly)
    except UnsupportedAssembly:
        return False
    root = db_root()
    # Prefer refGeneWithVer; fall back to refGene
    candidates = [
        root / f"{buildver}_refGeneWithVer.txt",
        root / f"{buildver}_refGene.txt",
    ]
    return root.is_dir() and any(p.is_file() for p in candidates)


def protocol_for_db(assembly: str) -> str:
    buildver = buildver_for_assembly(assembly)
    root = db_root()
    if (root / f"{buildver}_refGeneWithVer.txt").is_file():
        return "refGeneWithVer"
    if (root / f"{buildver}_refGene.txt").is_file():
        return "refGene"
    raise EngineNotReady(f"No refGene database found for {buildver} under {root}")


def supported_assemblies() -> list[str]:
    return ["GRCh37", "GRCh38"]


def ready_assemblies() -> list[str]:
    return [a for a in supported_assemblies() if is_db_ready(a)]


def docker_available() -> bool:
    return shutil.which("docker") is not None


def local_bin_ready() -> bool:
    return Path(settings.ANNOVAR_TABLE_BIN).is_file()


def runner_ready() -> bool:
    mode = settings.ANNOVAR_MODE
    if mode == "local":
        return local_bin_ready()
    if mode == "docker":
        return docker_available()
    # auto
    return local_bin_ready() or docker_available()


def assembly_meta(assembly: str) -> dict[str, Any]:
    try:
        buildver = buildver_for_assembly(assembly)
    except UnsupportedAssembly:
        return {"assembly": assembly, "ready": False}
    ready = is_db_ready(assembly)
    protocol = None
    if ready:
        try:
            protocol = protocol_for_db(assembly)
        except EngineNotReady:
            protocol = None
    return {
        "assembly": assembly,
        "ready": ready,
        "buildver": buildver,
        "protocol": protocol,
        "software_version": settings.ANNOVAR_VERSION_LABEL,
    }


def engine_info() -> dict[str, Any]:
    ready_list = ready_assemblies() if runner_ready() else []
    ready = bool(ready_list) and runner_ready()
    return {
        "id": "annovar",
        "name": "ANNOVAR",
        "version": settings.ANNOVAR_VERSION_LABEL,
        "supported_assemblies": supported_assemblies(),
        "ready_assemblies": ready_list,
        "ready": ready,
        "default_assembly": "GRCh38",
        "mode": settings.ANNOVAR_MODE,
        "license_note": "Confirm ANNOVAR redistribution/online-service rights before public exposure.",
        "assemblies_meta": {
            assembly: assembly_meta(assembly) for assembly in supported_assemblies()
        },
    }


def to_avinput_line(raw: str) -> tuple[str, str]:
    """Return (original, avinput line without trailing sample cols)."""
    original = raw.strip()
    norm = normalize_variant(original)
    # VEP region: chrom start end ref/alt strand
    m = re.match(
        r"^(\d+|X|Y|MT)\s+(\d+)\s+(\d+)\s+([ACGT-]+)/([ACGT-]+)\s*[+-]?",
        norm,
        re.IGNORECASE,
    )
    if not m:
        raise EngineFailed(f"Cannot convert variant to ANNOVAR avinput: {original}")
    chrom, start, end, ref, alt = m.groups()
    return original, f"{chrom}\t{start}\t{end}\t{ref}\t{alt}"


def _parse_aachange_entry(
    entry: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Parse one AAChange item → (gene, feature, cdot, protein)."""
    parts = [p for p in entry.split(":") if p]
    if not parts:
        return None, None, None, None
    gene = parts[0] if parts else None
    feature = parts[1] if len(parts) > 1 else None
    cdot = next((p for p in parts if p.startswith("c.")), None)
    protein = next((p for p in parts if p.startswith("p.")), None)
    if cdot and feature:
        cdot = f"{feature}:{cdot}"
    if protein and feature:
        protein = f"{feature}:{protein}"
    return gene, feature, cdot, protein


def _transcript_record(
    gene: str | None,
    feature: str | None,
    cdot: str | None,
    protein: str | None,
    *,
    rank: int,
    preferred: bool,
    source_index: int,
) -> dict[str, Any]:
    mane_status = None
    if rank == 0:
        mane_status = "select"
    elif rank == 1:
        mane_status = "plus_clinical"
    return {
        "gene": gene,
        "feature": feature,
        "cdot": cdot,
        "protein": protein,
        "preferred": preferred,
        "mane": rank < 100,
        "mane_status": mane_status,
        "source_index": source_index,
    }


def _parse_aachange(aachange: str) -> dict[str, Any]:
    """Parse all AAChange isoforms; core = MANE Select > Plus Clinical > first listed."""
    empty = {
        "feature": None,
        "cdot": None,
        "protein": None,
        "pick_reason": None,
        "transcript_count": 0,
        "canonical": None,
        "transcripts": [],
        "picked_index": None,
    }
    if not aachange or aachange == ".":
        return empty

    entries = [e.strip() for e in aachange.split(",") if e.strip() and e.strip() != "."]
    if not entries:
        return empty

    scored: list[tuple[int, int, tuple[str | None, str | None, str | None, str | None]]] = []
    for idx, entry in enumerate(entries):
        parsed = _parse_aachange_entry(entry)
        _gene, feature, _cdot, _protein = parsed
        rank = mane_rank_from_accession(feature)
        scored.append((rank, idx, parsed))

    scored.sort(key=lambda x: (x[0], x[1]))
    best_rank, best_idx, (_g, feature, cdot, protein) = scored[0]
    pick_reason = pick_reason_for_rank(best_rank)
    canonical = "YES" if best_rank < 100 else None

    transcripts = [
        _transcript_record(
            g,
            feat,
            cd,
            prot,
            rank=rank,
            preferred=False,
            source_index=idx,
        )
        for rank, idx, (g, feat, cd, prot) in scored
    ]
    for i, t in enumerate(transcripts):
        t["preferred"] = i == 0

    return {
        "feature": feature,
        "cdot": cdot,
        "protein": protein,
        "pick_reason": pick_reason,
        "transcript_count": len(entries),
        "canonical": canonical,
        "picked_index": best_idx,
        "transcripts": transcripts,
    }


def parse_multianno(
    path: Path, input_by_key: dict[str, str]
) -> list[VariantResult]:
    results: list[VariantResult] = []
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            chrom = (row.get("Chr") or "").removeprefix("chr")
            start = row.get("Start", "")
            end = row.get("End", "")
            ref = row.get("Ref", "")
            alt = row.get("Alt", "")
            key = f"{chrom}:{start}:{end}:{ref}:{alt}"
            display = input_by_key.get(key, f"{chrom}:{start} {ref}>{alt}")

            gene = row.get("Gene.refGeneWithVer") or row.get("Gene.refGene") or None
            if gene == ".":
                gene = None
            func = row.get("Func.refGeneWithVer") or row.get("Func.refGene") or ""
            exonic = (
                row.get("ExonicFunc.refGeneWithVer")
                or row.get("ExonicFunc.refGene")
                or ""
            )
            consequence = ",".join(x for x in [func, exonic] if x and x != ".")
            aachange = (
                row.get("AAChange.refGeneWithVer")
                or row.get("AAChange.refGene")
                or ""
            )
            picked = _parse_aachange(aachange)

            results.append(
                VariantResult(
                    input=display,
                    allele=alt if alt != "." else None,
                    gene=gene,
                    feature=picked["feature"],
                    consequence=consequence or None,
                    cdot=picked["cdot"],
                    protein=picked["protein"],
                    canonical=picked["canonical"],
                    engine="annovar",
                    transcripts=picked.get("transcripts") or [],
                    details={
                        "annovar": dict(row),
                        "transcript_pick": {
                            "reason": picked["pick_reason"],
                            "transcript_count": picked["transcript_count"],
                            "picked_index": picked.get("picked_index"),
                        },
                    },
                )
            )
    return results


def _run_local(work: Path, avinput: Path, buildver: str, protocol: str) -> Path:
    out_prefix = work / "out"
    cmd = [
        "perl",
        settings.ANNOVAR_TABLE_BIN,
        str(avinput.name),
        str(settings.ANNOVAR_DB_DIR),
        "-buildver",
        buildver,
        "-out",
        str(out_prefix.name),
        "-remove",
        "-protocol",
        protocol,
        "-operation",
        "g",
        "-nastring",
        ".",
        "--argument",
        "-hgvs -splicing_threshold 10",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(work),
        capture_output=True,
        text=True,
        timeout=settings.ANNOVAR_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise EngineFailed(
            f"ANNOVAR failed (exit {result.returncode}): "
            f"{(result.stderr or result.stdout)[:500]}"
        )
    multianno = work / f"out.{buildver}_multianno.txt"
    if not multianno.is_file():
        raise EngineFailed("ANNOVAR finished but multianno output missing")
    return multianno


def _run_docker(work: Path, avinput: Path, buildver: str, protocol: str) -> Path:
    if not docker_available():
        raise EngineNotReady("docker not available for ANNOVAR_MODE=docker/auto")

    db_dir = str(db_root().resolve())
    work_dir = str(work.resolve())
    image = settings.ANNOVAR_DOCKER_IMAGE
    table = settings.ANNOVAR_TABLE_BIN  # path inside container

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{db_dir}:/humandb:ro",
        "-v",
        f"{work_dir}:/work",
        "-w",
        "/work",
        image,
        "perl",
        table,
        avinput.name,
        "/humandb/",
        "-buildver",
        buildver,
        "-out",
        "out",
        "-remove",
        "-protocol",
        protocol,
        "-operation",
        "g",
        "-nastring",
        ".",
        "--argument",
        "-hgvs -splicing_threshold 10",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.ANNOVAR_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise EngineFailed(
            f"ANNOVAR docker failed (exit {result.returncode}): "
            f"{(result.stderr or result.stdout)[:500]}"
        )
    multianno = work / f"out.{buildver}_multianno.txt"
    if not multianno.is_file():
        raise EngineFailed("ANNOVAR docker finished but multianno output missing")
    return multianno


def run_annovar(variants: list[str], assembly: str) -> list[VariantResult]:
    buildver = buildver_for_assembly(assembly)
    if not is_db_ready(assembly):
        raise EngineNotReady(
            f"ANNOVAR database for {assembly}/{buildver} not found under {db_root()}"
        )
    if not runner_ready():
        raise EngineNotReady(
            "ANNOVAR runner not ready (set ANNOVAR_MODE=local with binaries, "
            "or ANNOVAR_MODE=docker with docker available)"
        )

    protocol = protocol_for_db(assembly)
    input_by_key: dict[str, str] = {}

    acquired = _semaphore().acquire(timeout=30)
    if not acquired:
        raise EngineNotReady("ANNOVAR concurrency limit reached; try again later.")

    try:
        with tempfile.TemporaryDirectory(prefix="annovar_") as tmp:
            work = Path(tmp)
            avinput = work / "input.avinput"
            lines: list[str] = []
            for raw in variants:
                original, line = to_avinput_line(raw)
                chrom, start, end, ref, alt = line.split("\t")
                input_by_key[f"{chrom}:{start}:{end}:{ref}:{alt}"] = original
                lines.append(line)
            avinput.write_text("\n".join(lines) + "\n", encoding="utf-8")

            use_local = settings.ANNOVAR_MODE == "local" or (
                settings.ANNOVAR_MODE == "auto" and local_bin_ready()
            )
            try:
                if use_local:
                    multianno = _run_local(work, avinput, buildver, protocol)
                else:
                    multianno = _run_docker(work, avinput, buildver, protocol)
            except subprocess.TimeoutExpired as exc:
                raise EngineTimeout(
                    f"ANNOVAR timed out (>{settings.ANNOVAR_TIMEOUT_SECONDS}s)"
                ) from exc
            except FileNotFoundError as exc:
                raise EngineFailed(str(exc)) from exc

            return parse_multianno(multianno, input_by_key)
    finally:
        _semaphore().release()
