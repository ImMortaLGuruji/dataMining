#!/usr/bin/env bash
set -e
echo "Starting Annapurna Stores Platform..."
cd "$(dirname "$0")/.."
docker compose up -d
echo "Checking service status..."
docker compose ps
echo "Platform started successfully."
