from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


ZONE_COORDINATES: dict[str, tuple[float, float]] = {
    "MR-2": (13.0827, 80.2707),
    "CHENNAI-SOUTH": (12.9250, 80.1000),
    "DEFAULT": (13.0827, 80.2707),
}


@dataclass
class ZoneSnapshot:
    rain_mm: float
    congestion_ratio: float
    outage_ratio: float
    platform_outage: bool


class WeatherIntegrationClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_rain_mm(self, zone: str) -> float:
        zone_key = zone.upper()
        lat, lon = ZONE_COORDINATES.get(zone_key, ZONE_COORDINATES["DEFAULT"])

        try:
            with httpx.Client(timeout=self.settings.integration_timeout_seconds) as client:
                response = client.get(
                    self.settings.weather_api_url,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "rain",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                current = payload.get("current", {})
                return float(current.get("rain", 0.0))
        except Exception:
            return 0.0


class TrafficIntegrationClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_congestion_ratio(self, zone: str) -> float:
        if not self.settings.traffic_api_url:
            return 0.25

        try:
            with httpx.Client(timeout=self.settings.integration_timeout_seconds) as client:
                response = client.get(self.settings.traffic_api_url, params={"zone": zone})
                response.raise_for_status()
                payload = response.json()
                if "congestion_ratio" in payload:
                    return float(payload["congestion_ratio"])
                if "traffic_index" in payload:
                    return float(payload["traffic_index"])
        except Exception:
            return 0.25

        return 0.25


class PlatformIntegrationClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_platform_status(self, zone: str) -> tuple[float, bool]:
        if not self.settings.platform_api_url:
            return 0.0, False

        try:
            with httpx.Client(timeout=self.settings.integration_timeout_seconds) as client:
                response = client.get(self.settings.platform_api_url, params={"zone": zone})
                response.raise_for_status()
                payload = response.json()
                outage_ratio = float(payload.get("outage_ratio", 0.0))
                is_outage = bool(payload.get("is_outage", outage_ratio > 0.0))
                return outage_ratio, is_outage
        except Exception:
            return 0.0, False


class ExternalSourceGateway:
    def __init__(self) -> None:
        self.weather_client = WeatherIntegrationClient()
        self.traffic_client = TrafficIntegrationClient()
        self.platform_client = PlatformIntegrationClient()

    def fetch_zone_snapshot(self, zone: str) -> ZoneSnapshot:
        rain_mm = self.weather_client.fetch_rain_mm(zone=zone)
        congestion_ratio = self.traffic_client.fetch_congestion_ratio(zone=zone)
        outage_ratio, platform_outage = self.platform_client.fetch_platform_status(zone=zone)
        return ZoneSnapshot(
            rain_mm=rain_mm,
            congestion_ratio=congestion_ratio,
            outage_ratio=outage_ratio,
            platform_outage=platform_outage,
        )
