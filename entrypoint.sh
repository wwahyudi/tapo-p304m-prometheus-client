#!/bin/sh
set -e

# Check for required env vars
: "${TAPO_USERNAME:?Environment variable TAPO_USERNAME must be set}"
: "${TAPO_PASSWORD:?Environment variable TAPO_PASSWORD must be set}"
: "${TAPO_IP_ADDRESS:?Environment variable TAPO_IP_ADDRESS must be set}"

exec python3 prometheus.py