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


def engine_info() -> dict[str, Any]:
    ready = bool(ready_assemblies()) and runner_ready()
    return {
        "id": "annovar",
        "name": "ANNOVAR",
        "version": settings.ANNOVAR_VERSION_LABEL,
        "supported_assemblies": supported_assemblies(),
        "ready_assemblies": ready_assemblies() if runner_ready() else [],
        "ready": ready,
        "default_assembly": "GRCh38",
        "mode": settings.ANNOVAR_MODE,
        "license_note": "Confirm ANNOVAR redistribution/online-service rights before public exposure.",
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


def _parse_aachange(aachange: str) -> tuple[str | None, str | None, str | None]:
    """Parse AAChange.refGene like GENE:NM_x:exonN:c.xxx:p.yyy"""
    if not aachange or aachange == ".":
        return None, None, None
    # Take first transcript entry
    first = aachange.split(",")[0]
    parts = first.split(":")
    feature = parts[1] if len(parts) > 1 else None
    cdot = next((p for p in parts if p.startswith("c.")), None)
    protein = next((p for p in parts if p.startswith("p.")), None)
    if cdot and feature:
        cdot = f"{feature}:{cdot}"
    if protein and feature:
        protein = f"{feature}:{protein}"
    return feature, cdot, protein


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
            feature, cdot, protein = _parse_aachange(aachange)

            results.append(
                VariantResult(
                    input=display,
                    allele=alt if alt != "." else None,
                    gene=gene,
                    feature=feature,
                    consequence=consequence or None,
                    cdot=cdot,
                    protein=protein,
                    engine="annovar",
                    details={"annovar": dict(row)},
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
