from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge

from src.utils.models import UserState


class LinkQualityPredictor:
    def __init__(self, window: int = 4) -> None:
        self.window = window
        self.model = Ridge(alpha=0.5)

    def _fit_global(self, users: dict[str, UserState]) -> bool:
        features: list[list[float]] = []
        targets: list[float] = []
        for user in users.values():
            history = user.history_channel_quality
            if len(history) <= self.window:
                continue
            for start in range(len(history) - self.window):
                segment = history[start : start + self.window]
                features.append(segment + [user.mobility_speed])
                targets.append(history[start + self.window])
        if len(features) < 6:
            return False
        self.model.fit(np.asarray(features, dtype=float), np.asarray(targets, dtype=float))
        return True

    def predict(self, user: UserState, users: dict[str, UserState] | None = None) -> float:
        fitted = self._fit_global(users) if users is not None else False
        history = user.history_channel_quality[-self.window :]
        if fitted and len(history) >= self.window:
            vector = np.asarray(history + [user.mobility_speed], dtype=float).reshape(1, -1)
            prediction = float(self.model.predict(vector)[0])
        elif history:
            prediction = 0.7 * history[-1] + 0.3 * (sum(history) / len(history))
        else:
            prediction = user.channel_quality
        return max(0.05, min(1.0, prediction))
