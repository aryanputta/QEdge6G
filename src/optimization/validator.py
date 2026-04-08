from __future__ import annotations

from src.optimization.constraints import find_violations
from src.utils.models import AllocationDecision, OptimizationInstance


def validate_decisions(instance: OptimizationInstance, decisions: list[AllocationDecision]) -> list[str]:
    return find_violations(instance, [decision.option_id for decision in decisions])

