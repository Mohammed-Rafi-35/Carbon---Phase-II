from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def register_artifact(
    *,
    registry_path: Path,
    artifact_path: Path,
    model_version: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {}
    else:
        registry = {}

    history = registry.get("history", [])
    history.append(
        {
            "registered_at": datetime.now(tz=timezone.utc).isoformat(),
            "model_version": model_version,
            "artifact": str(artifact_path),
            "metrics": metrics,
        }
    )

    updated = {
        "active_version": model_version,
        "active_artifact": str(artifact_path),
        "history": history[-30:],
    }
    registry_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return updated
