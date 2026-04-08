from __future__ import annotations

import numpy as np

from src.ml.congestion_predictor import CongestionPredictor
from src.ml.demand_forecaster import DemandForecaster
from src.ml.link_quality_predictor import LinkQualityPredictor
from src.utils.models import UserState


class InferencePipeline:
    def __init__(self, enable_ai: bool) -> None:
        self.enable_ai = enable_ai
        self.demand_forecaster = DemandForecaster()
        self.link_predictor = LinkQualityPredictor()
        self.congestion_predictor = CongestionPredictor()

    def update_predictions(self, users: dict[str, UserState], horizon: int = 1, forecast_error_std: float = 0.0) -> None:
        for user in users.values():
            if self.enable_ai:
                user.predicted_demand_mbps = self.demand_forecaster.predict_horizon(user, users=users, horizon=horizon)
                if forecast_error_std > 0.0:
                    noise = np.random.normal(0.0, forecast_error_std * user.predicted_demand_mbps)
                    user.predicted_demand_mbps = max(0.1, user.predicted_demand_mbps + noise)
                user.channel_quality = self.link_predictor.predict(user, users=users)
            else:
                user.predicted_demand_mbps = user.demand_mbps
