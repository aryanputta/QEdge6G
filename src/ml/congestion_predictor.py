from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from src.ml.features import congestion_features


class CongestionPredictor:
    def __init__(self) -> None:
        self.model = RandomForestRegressor(n_estimators=24, random_state=7, max_depth=4)
        self._fitted = False

    def fit(self, samples: list[dict[str, float]], labels: list[float]) -> None:
        if len(samples) < 12:
            return
        matrix = np.asarray(
            [[sample["path_utilization"], sample["queue_delay_ms"], sample["loss_rate"]] for sample in samples],
            dtype=float,
        )
        self.model.fit(matrix, np.asarray(labels, dtype=float))
        self._fitted = True

    def predict_score(self, path_utilization: float, queue_delay_ms: float, loss_rate: float) -> float:
        features = congestion_features(path_utilization, queue_delay_ms, loss_rate)
        if self._fitted:
            vector = np.asarray(
                [[features["path_utilization"], features["queue_delay_ms"], features["loss_rate"]]],
                dtype=float,
            )
            return float(np.clip(self.model.predict(vector)[0], 0.0, 1.0))
        return min(1.0, 0.55 * features["path_utilization"] + 0.003 * features["queue_delay_ms"] + 2.0 * features["loss_rate"])
