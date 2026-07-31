"""VEP engine: readiness, subprocess runner, JSON parse."""

from __future__ import annotations

import json
import os
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
    # Expect info.txt inside Ensembl cache layout
    return (path / "info.txt").is_file() or any(path.iterdir())


def supported_assemblies() -> list[str]:
    return sorted(settings.VEP_ASSEMBLY_CACHE.keys())


def ready_assemblies() -> list[str]:
    return [a for a in supported_assemblies() if is_assembly_ready(a)]


def engine_info() -> dict[str, Any]:
    return {
        "id": "vep",
        "name": "Ensembl VEP",
        "version": "116",
        "supported_assemblies": supported_assemblies(),
        "ready_assemblies": ready_assemblies(),
        "ready": bool(ready_assemblies()),
        "default_assembly": settings.VEP_ASSEMBLY_DEFAULT,
    }


def parse_vep_output(
    raw: list[dict[str, Any]], input_map: dict[str, str] | None = None
) -> list[VariantResult]:
    results: list[VariantResult] = []
    input_map = input_map or {}

    for entry in raw:
        vep_input = entry.get("input", "")
        display_input = input_map.get(vep_input, vep_input)
        transcript_consequences = entry.get("transcript_consequences", [])

        if not transcript_consequences:
            results.append(VariantResult(input=display_input, engine="vep"))
            continue

        tc = transcript_consequences[0]
        results.append(
            VariantResult(
                input=display_input,
                allele=tc.get("variant_allele"),
                gene=tc.get("gene_symbol") or tc.get("gene_id"),
                feature=tc.get("transcript_id"),
                consequence=",".join(tc.get("consequence_terms", [])),
                impact=tc.get("impact"),
                cdot=tc.get("hgvsc"),
                protein=tc.get("hgvsp"),
                biotype=tc.get("biotype"),
                canonical=("YES" if tc.get("canonical") == 1 else None),
                engine="vep",
                details={"vep": {"transcript_consequence": tc}},
            )
        )
    return results


def run_vep(variants: list[str], assembly: str) -> list[VariantResult]:
    if assembly not in settings.VEP_ASSEMBLY_CACHE:
        raise UnsupportedAssembly(f"Unsupported assembly: {assembly}")

    if not is_assembly_ready(assembly):
        raise EngineNotReady(
            f"VEP cache for {assembly} is not ready under {settings.VEP_CACHE_DIR}. "
            "See scripts/download_vep_cache.sh and reference-manifest.yaml."
        )

    # VEP --dir_cache points at parent containing species dirs (e.g. homo_sapiens_merged)
    dir_cache = str(cache_root())
    vep_bin = settings.VEP_BIN

    normalized_map: dict[str, str] = {}
    input_file = ""
    output_file = ""

    acquired = _semaphore().acquire(timeout=30)
    if not acquired:
        raise EngineNotReady("VEP concurrency limit reached; try again later.")

    try:
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
            "perl",
            vep_bin,
            "--cache",
            "--merged",
            "--dir_cache",
            dir_cache,
            "--assembly",
            assembly,
            "--hgvs",
            "--symbol",
            "--canonical",
            "--pick",
            "--no_stats",
            "--json",
            "-i",
            input_file,
            "-o",
            output_file,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.VEP_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise EngineFailed(f"VEP binary not found at {vep_bin}") from exc
        except subprocess.TimeoutExpired as exc:
            raise EngineTimeout(
                f"VEP annotation timed out (>{settings.VEP_TIMEOUT_SECONDS}s)"
            ) from exc

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise EngineFailed(f"VEP failed (exit {result.returncode}): {stderr[:500]}")

        raw: list[dict[str, Any]] = []
        with open(output_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    raw.append(json.loads(line))

        return parse_vep_output(raw, normalized_map)
    finally:
        _semaphore().release()
        for tmp in (input_file, output_file):
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
