from __future__ import annotations

import numpy as np

from src.optimization.qubo_builder import build_qubo


def test_qubo_matrix_is_symmetric_and_has_slack_variables(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    qubo = build_qubo(instance)
    assert qubo.matrix.shape[0] == qubo.matrix.shape[1]
    assert np.allclose(qubo.matrix, qubo.matrix.T)
    assert qubo.metadata["num_slack_variables"] > 0

