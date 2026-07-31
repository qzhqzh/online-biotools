"""VEP engine: readiness, local/docker subprocess runner, JSON parse."""

from __future__ import annotations

import json
import os
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
    is_refseq_accession,
    mane_rank_from_vep_tc,
    pick_reason_for_rank,
    sort_key_for_transcript,
)
from apps.annotations.normalize import normalize_variant

_vep_semaphore: threading.Semaphore | None = None
_sem_lock = threading.Lock()


def _semaphore() -> threading.Semaphore:
    global _vep_semaphore
    with _sem_lock:
        if _vep_semaphore is None:
            _vep_semaphore = threading.Semaphore(settings.VEP_MAX_CONCURRENCY)
        return _vep_semaphore


def cache_root() -> Path:
    return Path(settings.VEP_CACHE_DIR)


def assembly_cache_path(assembly: str) -> Path | None:
    rel = settings.VEP_ASSEMBLY_CACHE.get(assembly)
    if not rel:
        return None
    return cache_root() / rel


def is_assembly_ready(assembly: str) -> bool:
    path = assembly_cache_path(assembly)
    if path is None or not path.is_dir():
        return False
    return (path / "info.txt").is_file() or any(path.iterdir())


def supported_assemblies() -> list[str]:
    return sorted(settings.VEP_ASSEMBLY_CACHE.keys())


def ready_assemblies() -> list[str]:
    return [assembly for assembly in supported_assemblies() if is_assembly_ready(assembly)]


def local_bin_ready() -> bool:
    return Path(settings.VEP_BIN).is_file()


def docker_available() -> bool:
    return shutil.which("docker") is not None


def runner_ready() -> bool:
    mode = settings.VEP_MODE
    if mode == "local":
        return local_bin_ready()
    if mode == "docker":
        return docker_available()
    return local_bin_ready() or docker_available()


def _use_docker() -> bool:
    mode = settings.VEP_MODE
    if mode == "docker":
        return True
    if mode == "local":
        return False
    return not local_bin_ready()


def _parse_cache_info(path: Path) -> dict[str, str]:
    """Parse Ensembl VEP cache info.txt (key\tvalue lines)."""
    meta: dict[str, str] = {}
    if not path.is_file():
        return meta
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return meta
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        meta[key.strip()] = value.strip()
    return meta


def assembly_meta(assembly: str) -> dict[str, Any]:
    """Public-facing cache / database version info for one assembly."""
    rel = settings.VEP_ASSEMBLY_CACHE.get(assembly, "")
    path = assembly_cache_path(assembly)
    ready = is_assembly_ready(assembly)
    info = _parse_cache_info(path / "info.txt") if path else {}
    cache_label = Path(rel).name if rel else assembly
    software = "116"
    if "_" in cache_label:
        software = cache_label.split("_", 1)[0]
    return {
        "assembly": assembly,
        "ready": ready,
        "cache_path": rel,
        "cache_label": cache_label,
        "software_version": software,
        "source_assembly": info.get("source_assembly") or info.get("assembly"),
        "gencode": info.get("source_gencode"),
        "genebuild": info.get("source_genebuild"),
        "refseq": info.get("source_refseq"),
        "dbsnp": info.get("source_dbSNP"),
        "gnomad_exomes": info.get("source_gnomADe"),
        "gnomad_genomes": info.get("source_gnomADg"),
        "clinvar": info.get("source_ClinVar"),
        "cosmic": info.get("source_COSMIC"),
    }


def engine_info() -> dict[str, Any]:
    ready_list = ready_assemblies() if runner_ready() else []
    ready = bool(ready_list) and runner_ready()
    assemblies_meta = {
        assembly: assembly_meta(assembly) for assembly in supported_assemblies()
    }
    return {
        "id": "vep",
        "name": "Ensembl VEP",
        "version": "116",
        "supported_assemblies": supported_assemblies(),
        "ready_assemblies": ready_list,
        "ready": ready,
        "default_assembly": settings.VEP_ASSEMBLY_DEFAULT,
        "mode": settings.VEP_MODE,
        "assemblies_meta": assemblies_meta,
    }


def _tc_to_hit(
    tc: dict[str, Any],
    *,
    preferred: bool,
    source_index: int,
    mane_rank: int,
) -> dict[str, Any]:
    mane_status = None
    if mane_rank == 0:
        mane_status = "select"
    elif mane_rank == 1:
        mane_status = "plus_clinical"
    return {
        "gene": tc.get("gene_symbol") or tc.get("gene_id"),
        "feature": tc.get("transcript_id"),
        "cdot": tc.get("hgvsc"),
        "protein": tc.get("hgvsp"),
        "consequence": ",".join(tc.get("consequence_terms") or []),
        "impact": tc.get("impact"),
        "biotype": tc.get("biotype"),
        "preferred": preferred,
        "mane": mane_rank < 100,
        "mane_status": mane_status,
        "canonical": tc.get("canonical") == 1,
        "source_index": source_index,
    }


def parse_vep_output(
    raw: list[dict[str, Any]], input_map: dict[str, str] | None = None
) -> list[VariantResult]:
    """Parse VEP JSON; core fields = MANE (or canonical) transcript; all hits in transcripts."""
    results: list[VariantResult] = []
    input_map = input_map or {}

    for entry in raw:
        vep_input = entry.get("input", "")
        display_input = input_map.get(vep_input, vep_input)
        transcript_consequences = entry.get("transcript_consequences") or []

        if not transcript_consequences:
            results.append(VariantResult(input=display_input, engine="vep"))
            continue

        scored: list[tuple[tuple, int, int, dict[str, Any]]] = []
        for index, consequence in enumerate(transcript_consequences):
            mane_rank = mane_rank_from_vep_tc(consequence)
            is_canonical = consequence.get("canonical") == 1
            refseq = is_refseq_accession(consequence.get("transcript_id"))
            scored.append(
                (
                    sort_key_for_transcript(
                        mane_rank,
                        is_canonical,
                        index,
                        refseq=refseq,
                    ),
                    mane_rank,
                    index,
                    consequence,
                )
            )

        scored.sort(key=lambda item: item[0])
        _key, best_rank, _best_index, preferred_tc = scored[0]
        is_canonical = preferred_tc.get("canonical") == 1
        preferred_refseq = is_refseq_accession(preferred_tc.get("transcript_id"))
        pick_reason = pick_reason_for_rank(
            best_rank,
            canonical=is_canonical and best_rank >= 100,
            refseq=preferred_refseq,
        )

        transcripts = [
            _tc_to_hit(
                consequence,
                preferred=(position == 0),
                source_index=source_index,
                mane_rank=mane_rank,
            )
            for position, (_key, mane_rank, source_index, consequence) in enumerate(
                scored
            )
        ]

        results.append(
            VariantResult(
                input=display_input,
                allele=preferred_tc.get("variant_allele"),
                gene=preferred_tc.get("gene_symbol") or preferred_tc.get("gene_id"),
                feature=preferred_tc.get("transcript_id"),
                consequence=",".join(preferred_tc.get("consequence_terms") or []),
                impact=preferred_tc.get("impact"),
                cdot=preferred_tc.get("hgvsc"),
                protein=preferred_tc.get("hgvsp"),
                biotype=preferred_tc.get("biotype"),
                canonical="YES" if best_rank < 100 or is_canonical else None,
                engine="vep",
                transcripts=transcripts,
                details={
                    "vep": {
                        "transcript_count": len(transcripts),
                        "pick_reason": pick_reason,
                        "transcript_consequence": preferred_tc,
                    },
                    "transcript_pick": {
                        "reason": pick_reason,
                        "transcript_count": len(transcripts),
                    },
                },
            )
        )
    return results


def _load_json_lines(path: Path) -> list[dict[str, Any]]:
    """Read VEP JSONL and convert malformed output into an engine error."""

    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EngineFailed(
                    f"VEP output contains invalid JSON at line {line_number}: {exc.msg}"
                ) from exc
            if not isinstance(payload, dict):
                raise EngineFailed(
                    f"VEP output line {line_number} is not a JSON object"
                )
            rows.append(payload)
    return rows


def _vep_cli_args(
    assembly: str,
    input_path: str,
    output_path: str,
    dir_cache: str,
) -> list[str]:
    return [
        "--cache",
        "--merged",
        "--dir_cache",
        dir_cache,
        "--assembly",
        assembly,
        "--hgvs",
        "--symbol",
        "--canonical",
        "--mane",
        "--no_stats",
        "--json",
        "--force_overwrite",
        "-i",
        input_path,
        "-o",
        output_path,
    ]


def _docker_cache_volumes(dir_cache: Path) -> list[str]:
    """Mount cache root; overlay symlink targets (Docker does not follow host symlinks)."""
    args = ["-v", f"{dir_cache.resolve()}:/opt/vep/.vep:ro"]
    for rel in settings.VEP_ASSEMBLY_CACHE.values():
        link = dir_cache / rel
        if not link.exists():
            continue
        resolved = link.resolve()
        if link.is_symlink() or resolved != link:
            container = f"/opt/vep/.vep/{rel}"
            args.extend(["-v", f"{resolved}:{container}:ro"])
    return args


def _run_local(
    assembly: str,
    input_file: Path,
    output_file: Path,
) -> subprocess.CompletedProcess[str]:
    dir_cache = str(cache_root().resolve())
    cmd = [
        "perl",
        settings.VEP_BIN,
        *_vep_cli_args(assembly, str(input_file), str(output_file), dir_cache),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.VEP_TIMEOUT_SECONDS,
    )


def _run_docker(
    assembly: str,
    work: Path,
    input_name: str,
    output_name: str,
) -> subprocess.CompletedProcess[str]:
    if not docker_available():
        raise EngineNotReady("docker not available for VEP_MODE=docker/auto")

    dir_cache = cache_root()
    image = settings.VEP_DOCKER_IMAGE
    work_dir = str(work.resolve())
    uid = os.getuid()
    gid = os.getgid()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "perl",
        "-u",
        f"{uid}:{gid}",
        *_docker_cache_volumes(dir_cache),
        "-v",
        f"{work_dir}:/work",
        "-w",
        "/work",
        image,
        "/opt/vep/src/ensembl-vep/vep",
        *_vep_cli_args(
            assembly,
            f"/work/{input_name}",
            f"/work/{output_name}",
            "/opt/vep/.vep",
        ),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.VEP_TIMEOUT_SECONDS,
    )


def run_vep(variants: list[str], assembly: str) -> list[VariantResult]:
    if assembly not in settings.VEP_ASSEMBLY_CACHE:
        raise UnsupportedAssembly(f"Unsupported assembly: {assembly}")

    if not is_assembly_ready(assembly):
        raise EngineNotReady(
            f"VEP cache for {assembly} is not ready under {settings.VEP_CACHE_DIR}. "
            "See scripts/download_vep_cache.sh and reference-manifest.yaml."
        )

    if not runner_ready():
        raise EngineNotReady(
            "VEP runner not ready (install local VEP_BIN, or set VEP_MODE=docker/auto with Docker)."
        )

    use_docker = _use_docker()
    normalized_map: dict[str, str] = {}

    acquired = _semaphore().acquire(timeout=30)
    if not acquired:
        raise EngineNotReady("VEP concurrency limit reached; try again later.")

    try:
        with tempfile.TemporaryDirectory(prefix="vep_") as tmp:
            work = Path(tmp)
            input_file = work / "input.txt"
            output_file = work / "output.json"

            with input_file.open("w", encoding="utf-8") as handle:
                for variant in variants:
                    normalized = normalize_variant(variant)
                    normalized_map[normalized] = variant.strip()
                    handle.write(normalized + "\n")

            try:
                if use_docker:
                    result = _run_docker(
                        assembly,
                        work,
                        input_file.name,
                        output_file.name,
                    )
                else:
                    result = _run_local(assembly, input_file, output_file)
            except FileNotFoundError as exc:
                raise EngineFailed(
                    f"VEP runner missing ({'docker' if use_docker else settings.VEP_BIN})"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise EngineTimeout(
                    f"VEP annotation timed out (>{settings.VEP_TIMEOUT_SECONDS}s)"
                ) from exc

            if result.returncode != 0:
                stderr = (result.stderr or result.stdout or "").strip()
                raise EngineFailed(
                    f"VEP failed (exit {result.returncode}): {stderr[:500]}"
                )

            if not output_file.is_file():
                raise EngineFailed("VEP finished but output JSON is missing")

            return parse_vep_output(_load_json_lines(output_file), normalized_map)
    finally:
        _semaphore().release()
