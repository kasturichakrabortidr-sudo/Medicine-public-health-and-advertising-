"""Shared dataclasses for the evidence pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


@dataclass
class EffectSize:
    metric: str
    value: float
    ci_low: float
    ci_high: float
    outcome: str
    excerpt: str


@dataclass
class Validation:
    status: str
    via: str
    identifier: str
    retrieved_at: str
    canonical_url: str


@dataclass
class EvidenceRecord:
    key: str
    title: str
    url: str
    source_connector: str
    source_family: str
    issuing_body: str
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    nct_id: str | None = None
    handle: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    is_oa: bool = False
    abstract: str = ""
    validation: Validation | None = None
    claims: list[str] = field(default_factory=list)
    effects: list[EffectSize] = field(default_factory=list)
    is_qualitative: bool = False
    is_guideline: bool = False
    snippets: list[str] = field(default_factory=list)
    citation_id: int | None = None

    def text_blob(self) -> str:
        return f"{self.title}\n{self.abstract}"
