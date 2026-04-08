from __future__ import annotations

from src.ml.inference_pipeline import InferencePipeline
from src.utils.models import UserState


def test_inference_pipeline_updates_predictions(optimization_instance):
    _, _, users, _, _, _ = optimization_instance
    for user in users.values():
        user.history_demand_mbps.extend([user.demand_mbps * 0.8, user.demand_mbps * 1.1])
        user.history_channel_quality.extend([0.55, 0.65])
    pipeline = InferencePipeline(enable_ai=True)
    before = {user.user_id: user.predicted_demand_mbps for user in users.values()}
    pipeline.update_predictions(users)
    after = {user.user_id: user.predicted_demand_mbps for user in users.values()}
    assert any(after[user_id] != before[user_id] for user_id in before)

