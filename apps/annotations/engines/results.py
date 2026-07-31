"""Shared annotation result DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VariantResult:
    input: str
    allele: str | None = None
    gene: str | None = None
    feature: str | None = None
    consequence: str | None = None
    impact: str | None = None
    cdot: str | None = None
    protein: str | None = None
    biotype: str | None = None
    canonical: str | None = None
    engine: str = "vep"
    # All isoform hits (e.g. ANNOVAR AAChange); preferred first. Top-level fields = preferred.
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "allele": self.allele,
            "gene": self.gene,
            "feature": self.feature,
            "consequence": self.consequence,
            "impact": self.impact,
            "cdot": self.cdot,
            "protein": self.protein,
            "biotype": self.biotype,
            "canonical": self.canonical,
            "engine": self.engine,
            "transcripts": self.transcripts,
            "details": self.details,
        }
