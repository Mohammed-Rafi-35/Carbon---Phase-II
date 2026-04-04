from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_trigger_scheduler_enabled_in_local_compose() -> None:
    compose = (BACKEND_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert 'ENABLE_SCHEDULER: "true"' in compose


def test_gateway_compose_has_all_upstream_targets() -> None:
    compose = (BACKEND_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    required_env = [
        "IDENTITY_SERVICE_URL",
        "ANALYTICS_SERVICE_URL",
        "CLAIMS_SERVICE_URL",
        "POLICY_SERVICE_URL",
        "FRAUD_SERVICE_URL",
        "PAYOUT_SERVICE_URL",
        "AI_SERVICE_URL",
        "NOTIFICATION_SERVICE_URL",
        "TRIGGER_SERVICE_URL",
        "REQUEST_TIMEOUT_SECONDS",
        "UPSTREAM_RETRY_ATTEMPTS",
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
        "RATE_LIMIT_PER_MINUTE",
        "MAX_REQUEST_BODY_BYTES",
    ]
    for key in required_env:
        assert key in compose, f"Missing gateway env in compose: {key}"


def test_monitoring_stack_configs_exist() -> None:
    assert (BACKEND_ROOT / "infrastructure/monitoring/prometheus/prometheus.yml").is_file()
    assert (
        BACKEND_ROOT / "infrastructure/monitoring/grafana/provisioning/datasources/prometheus.yml"
    ).is_file()


def test_deployment_automation_scripts_are_present_and_non_empty() -> None:
    scripts = [
        BACKEND_ROOT / "infrastructure/scripts/setup.sh",
        BACKEND_ROOT / "infrastructure/scripts/migrate.sh",
        BACKEND_ROOT / "infrastructure/scripts/deploy.sh",
        BACKEND_ROOT / "infrastructure/scripts/rollback.sh",
    ]
    for script in scripts:
        assert script.is_file(), f"Missing script: {script}"
        assert script.read_text(encoding="utf-8").strip(), f"Script is empty: {script}"
