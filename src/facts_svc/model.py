"""Typed, renderer-independent models for reusable FACTS schematics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class BranchKind(str, Enum):
    """Supported shunt branches in a conceptual SVC schematic."""

    TCR = "TCR"
    TSR = "TSR"
    TSC = "TSC"
    FC = "FC"
    FILTER = "FILTER"


@dataclass(frozen=True)
class Branch:
    """One independently identified SVC shunt branch.

    ``harmonic_order`` applies only to a single-tuned LC filter.  The model
    defines a topology, not reactor/capacitor sizing or a power-flow solution.
    """

    name: str
    kind: BranchKind
    harmonic_order: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Branch name must be a nonempty string")
        if not isinstance(self.kind, BranchKind):
            object.__setattr__(self, "kind", BranchKind(str(self.kind).upper()))
        if self.kind is BranchKind.FILTER:
            if isinstance(self.harmonic_order, bool) or not isinstance(self.harmonic_order, int):
                raise ValueError("FILTER branches need a positive integer harmonic_order")
            if self.harmonic_order < 2:
                raise ValueError("The filter harmonic order must be at least 2")
        elif self.harmonic_order is not None:
            raise ValueError("harmonic_order is only permitted for FILTER branches")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Branch:
        if not isinstance(data, Mapping):
            raise ValueError("Each branch must be a JSON object")
        return cls(
            name=data["name"],
            kind=BranchKind(str(data["kind"]).upper()),
            harmonic_order=data.get("harmonic_order"),
        )

    def to_dict(self) -> dict[str, str | int]:
        result: dict[str, str | int] = {"name": self.name, "kind": self.kind.value}
        if self.harmonic_order is not None:
            result["harmonic_order"] = self.harmonic_order
        return result


@dataclass(frozen=True)
class SVCConfig:
    """Configuration for a functional single-line/per-phase SVC diagram."""

    title: str
    branches: tuple[Branch, ...]
    transformer: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("SVC title must be a nonempty string")
        branches = tuple(self.branches)
        if not 1 <= len(branches) <= 12:
            raise ValueError("An SVC must contain between 1 and 12 branches")
        if any(not isinstance(b, Branch) for b in branches):
            raise TypeError("All branches must be Branch objects")
        if len({b.name.casefold() for b in branches}) != len(branches):
            raise ValueError("Branch names must be unique (case-insensitive)")
        if not isinstance(self.transformer, bool):
            raise ValueError("transformer must be true or false")
        object.__setattr__(self, "branches", branches)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SVCConfig:
        if not isinstance(data, Mapping):
            raise ValueError("The configuration must be a JSON object")
        branches = data.get("branches", [])
        if not isinstance(branches, list):
            raise ValueError("branches must be a JSON array")
        return cls(
            title=data["title"],
            branches=tuple(Branch.from_dict(b) for b in branches),
            transformer=data.get("transformer", True),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> SVCConfig:
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "transformer": self.transformer,
            "branches": [branch.to_dict() for branch in self.branches],
        }


def presets() -> dict[str, SVCConfig]:
    """Return fresh, immutable SVC diagram examples."""
    return {
        "tcr-only": SVCConfig("Thyristor-controlled reactor (TCR)", (Branch("TCR 1", BranchKind.TCR),)),
        "fc-tcr": SVCConfig("Fixed capacitor + TCR (FC-TCR)", (
            Branch("FC 1", BranchKind.FC), Branch("TCR 1", BranchKind.TCR),
        )),
        "tsc-tcr": SVCConfig("Thyristor-switched capacitor + TCR", (
            Branch("TSC 1", BranchKind.TSC), Branch("TCR 1", BranchKind.TCR),
        )),
        "hybrid": SVCConfig("Hybrid SVC: TSC, TCR and harmonic filters", (
            Branch("TSC 1", BranchKind.TSC),
            Branch("TSC 2", BranchKind.TSC),
            Branch("TCR 1", BranchKind.TCR),
            Branch("5th filter", BranchKind.FILTER, harmonic_order=5),
            Branch("7th filter", BranchKind.FILTER, harmonic_order=7),
        )),
        "multi-tsc": SVCConfig("Multi-bank SVC: three TSC steps + TCR", (
            Branch("TSC 1", BranchKind.TSC),
            Branch("TSC 2", BranchKind.TSC),
            Branch("TSC 3", BranchKind.TSC),
            Branch("TCR 1", BranchKind.TCR),
        )),
        "tsr-fc": SVCConfig("Thyristor-switched reactor + fixed capacitor", (
            Branch("FC 1", BranchKind.FC), Branch("TSR 1", BranchKind.TSR),
        )),
    }
