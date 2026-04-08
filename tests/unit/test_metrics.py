from __future__ import annotations

from src.utils.metrics import jain_fairness


def test_jain_fairness_known_value():
    fairness = jain_fairness([1.0, 1.0, 1.0, 1.0])
    assert fairness == 1.0

