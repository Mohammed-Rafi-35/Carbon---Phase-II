#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <previous_version_tag> [environment]" >&2
  exit 1
fi

TARGET_VERSION="$1"
ENVIRONMENT="${2:-prod}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

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

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "Compose file not found: ${COMPOSE_FILE}" >&2
  exit 1
fi

export CARBON_VERSION="${TARGET_VERSION}"
echo "Rolling back '${ENVIRONMENT}' stack to CARBON_VERSION=${CARBON_VERSION}"
docker compose -f "${COMPOSE_FILE}" up -d
docker compose -f "${COMPOSE_FILE}" ps

echo "Rollback completed."