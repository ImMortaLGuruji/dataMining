#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 scripts/collect-evidence.py || python scripts/collect-evidence.py || py scripts/collect-evidence.py
