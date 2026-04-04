#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ENVIRONMENT="${1:-dev}"

"${SCRIPT_DIR}/setup.sh" "${ENVIRONMENT}"
"${SCRIPT_DIR}/migrate.sh" "${ENVIRONMENT}"

echo "Deployment flow completed for '${ENVIRONMENT}'."