from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.utils.helpers import clamp


ZONE_COORDINATE_MAP: dict[str, tuple[float, float]] = {
    "Z1": (13.0827, 80.2707),
    "LR-1": (13.0827, 80.2707),
    "MR-2": (12.9716, 77.5946),
    "HR-3": (19.0760, 72.8777),
}


class PublicSignalClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._http = httpx.Client(timeout=settings.external_signal_timeout_seconds)

    def fetch_weather_adjustment(self, zone: str) -> float:
        coords = ZONE_COORDINATE_MAP.get(zone.upper())
        if not coords:
            return 0.0

        latitude, longitude = coords
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "precipitation,wind_speed_10m",
            "timezone": "auto",
        }

        try:
            response = self._http.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            body: dict[str, Any] = response.json()
            current = body.get("current", {})
            precipitation = float(current.get("precipitation", 0.0))
            wind = float(current.get("wind_speed_10m", 0.0))
            adjustment = (precipitation * 0.015) + (wind * 0.002)
            return clamp(adjustment, 0.0, 0.15)
        except Exception:
            return 0.0

    def blend_with_metrics(self, zone: str, metrics: dict[str, float]) -> dict[str, float]:
        adjustment = self.fetch_weather_adjustment(zone)
        if adjustment <= 0:
            return metrics

        blended = dict(metrics)
        blended["disruption_freq"] = clamp(blended["disruption_freq"] + adjustment)
        blended["duration"] = clamp(blended["duration"] + (adjustment * 0.8))
        return blended
