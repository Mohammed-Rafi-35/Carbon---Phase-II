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

if ! command -v docker >/dev/null 2>&1; then
	echo "docker is required but was not found in PATH." >&2
	exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
	echo "docker compose plugin is required but not available." >&2
	exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
	echo "Compose file not found: ${COMPOSE_FILE}" >&2
	exit 1
fi

echo "Using compose file: ${COMPOSE_FILE}"
docker compose -f "${COMPOSE_FILE}" pull --ignore-pull-failures
docker compose -f "${COMPOSE_FILE}" up -d --build
docker compose -f "${COMPOSE_FILE}" ps

echo "Setup complete for '${ENVIRONMENT}'."
