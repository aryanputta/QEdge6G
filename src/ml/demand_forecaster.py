from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge

from src.ml.features import demand_features
from src.utils.models import UserState


class DemandForecaster:
    def __init__(self, alpha: float = 0.55, window: int = 4) -> None:
        self.alpha = alpha
        self.window = window
        self.model = Ridge(alpha=1.0)

    def _fit_global(self, users: dict[str, UserState]) -> bool:
        features: list[list[float]] = []
        targets: list[float] = []
        for user in users.values():
            history = user.history_demand_mbps
            if len(history) <= self.window:
                continue
            for start in range(len(history) - self.window):
                segment = history[start : start + self.window]
                target = history[start + self.window]
                features.append(segment)
                targets.append(target)
        if len(features) < 6:
            return False
        self.model.fit(np.asarray(features, dtype=float), np.asarray(targets, dtype=float))
        return True

    def predict(self, user: UserState, users: dict[str, UserState] | None = None) -> float:
        if users is not None:
            fitted = self._fit_global(users)
        else:
            fitted = False
        features = demand_features(user)
        baseline = features["mean_recent_demand"]
        if fitted and len(user.history_demand_mbps) >= self.window:
            vector = np.asarray(user.history_demand_mbps[-self.window :], dtype=float).reshape(1, -1)
            prediction = float(self.model.predict(vector)[0])
        else:
            prediction = self.alpha * features["latest_demand"] + (1.0 - self.alpha) * baseline
        return max(0.5, prediction)

    def predict_horizon(self, user: UserState, users: dict[str, UserState], horizon: int) -> float:
        horizon = max(1, horizon)
        history = list(user.history_demand_mbps[-self.window :]) or [user.demand_mbps]
        predictions = []
        for _ in range(horizon):
            temp_user = UserState(**{**user.__dict__, "history_demand_mbps": list(history)})
            prediction = self.predict(temp_user, users=users)
            predictions.append(prediction)
            history.append(prediction)
            history = history[-self.window :]
        return float(np.mean(predictions))
