#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 scripts/validate.py || python scripts/validate.py || py scripts/validate.py
