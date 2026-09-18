#!/usr/bin/env bash
set -e
echo "Stopping Annapurna Stores Platform..."
cd "$(dirname "$0")/.."
docker compose stop
echo "Platform stopped."
