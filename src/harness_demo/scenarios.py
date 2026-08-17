from __future__ import annotations

from pathlib import Path

import yaml

from harness_demo.domain import IncidentScenario


REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_ROOT = REPO_ROOT / "cases"


def load_incident_scenario(scenario_id: str) -> IncidentScenario:
    scenario_dir = CASES_ROOT / scenario_id
    raw = yaml.safe_load((scenario_dir / "scenario.yaml").read_text(encoding="utf-8"))
    return IncidentScenario(
        id=raw["id"],
        name=raw["name"],
        incident=raw["incident"],
        expected=raw["expected"],
        score_weights=raw["score_weights"],
        logs=(scenario_dir / "logs" / "checkout.log").read_text(encoding="utf-8"),
        runbook=(scenario_dir / "runbooks" / "checkout-promotion.md").read_text(encoding="utf-8"),
        prior_memory=(scenario_dir / "memory" / "prior-incident.md").read_text(encoding="utf-8"),
    )
