#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ENVIRONMENT="${1:-dev}"

resolve_compose_file() {
	case "$1" in
		dev)
			echo "${BACKEND_ROOT}/infrastructure/docker/docker-compose.dev.yml"
			;;
		staging)
			echo "${BACKEND_ROOT}/infrastructure/docker/docker-compose.prod.yml"
			;;
		prod)
			echo "${BACKEND_ROOT}/infrastructure/docker/docker-compose.prod.yml"
			;;
		local)
			echo "${BACKEND_ROOT}/docker-compose.yml"
			;;
		*)
			echo "Unsupported environment '$1'. Use one of: dev, staging, prod, local." >&2
			exit 1
			;;
	esac
}

COMPOSE_FILE="$(resolve_compose_file "${ENVIRONMENT}")"

services=(
	identity-service
	policy-pricing-service
	claims-service
	fraud-service
	payout-service
	notification-service
	analytics-service
	trigger-service
	ai-risk-service
)

if ! command -v docker >/dev/null 2>&1; then
	echo "docker is required but was not found in PATH." >&2
	exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
	echo "Compose file not found: ${COMPOSE_FILE}" >&2
	exit 1
fi

for service in "${services[@]}"; do
	echo "Running migrations for ${service}"
	docker compose -f "${COMPOSE_FILE}" exec -T "${service}" alembic upgrade head
done

echo "Migrations completed for '${ENVIRONMENT}'."
