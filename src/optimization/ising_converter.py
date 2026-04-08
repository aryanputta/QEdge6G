from __future__ import annotations

import numpy as np

from src.optimization.qubo_builder import QUBOModel


def qubo_to_ising(qubo: QUBOModel) -> tuple[np.ndarray, np.ndarray, float]:
    q = qubo.matrix
    n = q.shape[0]
    h = np.zeros(n, dtype=float)
    j = np.zeros((n, n), dtype=float)
    offset = qubo.constant

    for i in range(n):
        offset += q[i, i] / 2.0
        h[i] -= q[i, i] / 2.0
    for i in range(n):
        for k in range(i + 1, n):
            if q[i, k] == 0:
                continue
            offset += q[i, k] / 4.0
            h[i] -= q[i, k] / 4.0
            h[k] -= q[i, k] / 4.0
            j[i, k] += q[i, k] / 4.0
            j[k, i] = j[i, k]
    return h, j, offset

