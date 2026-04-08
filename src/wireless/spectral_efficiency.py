from __future__ import annotations

import math


def spectral_efficiency_from_quality(channel_quality: float) -> float:
    snr_linear = max(0.1, 1.0 + 24.0 * channel_quality)
    return max(0.3, min(8.0, math.log2(1.0 + snr_linear)))

