"""Research registry checks that distinguish evidence from benchmark interpretation."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .config import load_yaml, resource_root


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    authors: list[str] = Field(min_length=1)
    year: int = Field(ge=1900, le=2100)
    status: str
    doi: str | None = None
    url: HttpUrl
    access_date: str
    informs: list[str] = Field(min_length=1)
    does_not_establish: str = Field(min_length=10)
    limitations: list[str] = Field(default_factory=list)


def check_registry(path: Path | None = None) -> list[SourceRecord]:
    registry_path = path or (resource_root() / "docs/research/SOURCE_REGISTRY.yaml")
    payload = load_yaml(registry_path)
    sources = [SourceRecord.model_validate(item) for item in payload["sources"]]
    ids = [source.id for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("source registry IDs must be unique")
    return sources
